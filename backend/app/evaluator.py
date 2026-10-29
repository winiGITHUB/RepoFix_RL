import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .agent import DemoAgent, OpenAICompatibleAgent
from .models import RunResult, TraceEvent
from .tasks import DemoTask


def evaluate(task: DemoTask, agent: DemoAgent | OpenAICompatibleAgent, run_id: str) -> RunResult:
    started = time.perf_counter()
    trace: list[TraceEvent] = [
        TraceEvent(step=1, kind="plan", title="分析任务", detail=task.summary.description),
        TraceEvent(step=2, kind="tool", title="读取 solution.py", detail=task.files["solution.py"]),
    ]
    edit = agent.propose_edit(task.summary.id, task.files)
    trace.append(TraceEvent(step=3, kind="reasoning", title="形成修复建议", detail=edit.rationale))

    with tempfile.TemporaryDirectory(prefix="repofix-") as directory:
        root = Path(directory)
        for relative, content in task.files.items():
            (root / relative).write_text(content, encoding="utf-8")
        (root / "test_solution.py").write_text(task.test_file, encoding="utf-8")
        target = (root / edit.path).resolve()
        if root.resolve() not in target.parents:
            raise ValueError("The agent edit path escapes the task workspace")
        target.write_text(edit.content, encoding="utf-8")
        trace.append(TraceEvent(step=4, kind="tool", title="应用补丁", detail=f"更新 {edit.path}"))

        completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "test_solution.py"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        output = (completed.stdout + completed.stderr).strip()[-2500:]
        total, passed = _parse_pytest_summary(output)
        trace.append(
            TraceEvent(
                step=5,
                kind="evaluation",
                title="运行隐藏测试",
                detail=output or f"pytest exited with code {completed.returncode}",
                status="passed" if completed.returncode == 0 else "failed",
            )
        )
        diff = _unified_diff(task.files[edit.path], edit.content, edit.path)

    elapsed = int((time.perf_counter() - started) * 1000)
    score = passed / total if total else 0.0
    status = "passed" if total > 0 and passed == total else "failed"
    return RunResult(
        run_id=run_id,
        task=task.summary,
        status=status,
        score=score,
        tests_passed=passed,
        tests_total=total,
        duration_ms=elapsed,
        summary=("所有测试通过，修复符合当前任务要求。" if status == "passed" else "仍有测试失败，请检查执行轨迹。"),
        diff=diff,
        trace=trace,
    )


def _parse_pytest_summary(output: str) -> tuple[int, int]:
    import re

    match = re.search(r"(\d+) passed(?:, (\d+) failed)?", output)
    if match:
        passed = int(match.group(1))
        failed = int(match.group(2) or 0)
        return passed, passed + failed
    failed_match = re.search(r"(\d+) failed", output)
    if failed_match:
        failed = int(failed_match.group(1))
        return 0, failed
    return 0, 0


def _unified_diff(before: str, after: str, path: str) -> str:
    import difflib

    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )
