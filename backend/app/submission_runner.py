import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run_submission(language: str, source_code: str, samples: list[dict]) -> dict:
    """Run a local submission with a strict timeout; not a security sandbox."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="codereview-") as folder:
        root = Path(folder)
        if language != "python":
            raise ValueError("only Python submissions are currently supported")
        source = root / "main.py"
        source.write_text(source_code, encoding="utf-8")
        command = [sys.executable, "-I", str(source)]
        try:
            cases = samples or [{"input": "", "expected_output": ""}]
            results = []
            for index, case in enumerate(cases, start=1):
                completed = subprocess.run(command, cwd=root, input=case.get("input", ""), capture_output=True, text=True, timeout=3, check=False)
                actual = completed.stdout.strip()
                expected = case.get("expected_output", "").strip()
                matched = completed.returncode == 0 and (not expected or actual == expected)
                results.append({"case": index, "passed": matched, "input": case.get("input", ""), "expected": expected, "actual": actual, "stderr": completed.stderr[-1500:], "exit_code": completed.returncode})
            all_passed = all(row["passed"] for row in results)
            summary = "\n".join(f"样例 {row['case']}: {'通过' if row['passed'] else '未通过'}\n期望: {row['expected']}\n实际: {row['actual']}" for row in results)
            return {"compile_status": "passed", "run_status": "passed" if all_passed else "failed", "stdout": summary, "stderr": "\n".join(row["stderr"] for row in results if row["stderr"]), "duration_ms": int((time.perf_counter()-started)*1000), "sample_results": results}
        except subprocess.TimeoutExpired as exc:
            return {"compile_status": "passed", "run_status": "timeout", "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "", "stderr": "程序运行超过 3 秒，已终止。", "duration_ms": int((time.perf_counter()-started)*1000), "sample_results": []}
