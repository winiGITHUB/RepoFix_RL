from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from .agent import DemoAgent, OpenAICompatibleAgent
from .evaluator import evaluate
from .models import RunRequest, RunResult, SubmissionResult, SubmissionRequest, TaskSummary, TraceEvent
from .submission_runner import run_submission
from .tasks import get_task, list_tasks

load_dotenv()

app = FastAPI(title="RepoFix-RL API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_agent() -> DemoAgent | OpenAICompatibleAgent:
    if os.getenv("AGENT_PROVIDER", "demo").lower() == "openai-compatible":
        return OpenAICompatibleAgent()
    return DemoAgent()


@app.get("/api/health")
def health() -> dict[str, str]:
    try:
        return {
            "status": "ok",
            "provider": get_agent().name,
        }
    except ValueError as exc:
        return {
            "status": "misconfigured",
            "provider": str(exc),
        }


@app.get("/api/tasks", response_model=list[TaskSummary])
def tasks() -> list[TaskSummary]:
    return list_tasks()


@app.post("/api/runs", response_model=RunResult)
def run_task(request: RunRequest) -> RunResult:
    try:
        task = get_task(request.task_id)
        return evaluate(task, get_agent(), run_id=str(uuid4()))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=408, detail="Evaluation timed out") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/submissions", response_model=SubmissionResult)
def diagnose_submission(request: SubmissionRequest) -> SubmissionResult:
    try:
        samples = [item.model_dump() for item in request.samples]
        execution = run_submission(request.language, request.source_code, samples)
        if execution["compile_status"] != "passed":
            # Do not let the model reinterpret a runner failure as an input/runtime bug.
            execution_output = execution["stderr"].strip()
            root_cause = execution_output or "Python 执行器未能完成运行。"
            hints = ["检查下方 PROGRAM OUTPUT 和样例输入，再根据具体错误调整代码。"]
            diagnosis = {
                "verdict": "执行器未完成运行。",
                "bug_category": "execution",
                "location": "Python 执行阶段",
                "counterexample": "无；样例尚未完成执行。",
                "root_cause": root_cause,
                "hints": hints,
                "solution_review": "由于执行器未完成运行，没有完整结果可用于评价算法逻辑或输入处理。",
                "suggested_patch": "",
            }
        else:
            diagnosis = get_agent().diagnose_submission(
                request.problem, request.language, request.source_code, execution
            )
            sample_results = execution["sample_results"]
            if sample_results and all(result["passed"] for result in sample_results):
                # Keep model-generated claims consistent with the observed sample results.
                diagnosis.update(
                    verdict="所提供样例全部通过，暂未复现错误。",
                    bug_category="none_observed",
                    location="当前已提供样例范围",
                    counterexample="未发现；所有已提供样例均通过。",
                    root_cause="现有运行结果不支持‘输入格式错误’或‘输出不正确’的判断。",
                    hints=[
                        "可以补充题目约束中的边界样例，继续验证未覆盖的情况。",
                        "当前样例通过只说明这些输入下结果正确，不代表已经验证所有可能输入。",
                    ],
                    solution_review="所有已提供样例均通过。建议结合题目约束补充边界测试；目前没有证据表明代码存在可复现错误。",
                    suggested_patch="",
                )
            else:
                failed = next((result for result in sample_results if not result["passed"]), None)
                if failed:
                    diagnosis["counterexample"] = (
                        f"样例 {failed['case']}：输入 {failed['input']!r}；"
                        f"期望 {failed['expected']!r}，实际 {failed['actual']!r}；"
                        f"退出码 {failed['exit_code']}。"
                    )
        trace = [
            TraceEvent(step=1, kind="tool", title="运行用户代码", detail=f"语言：{request.language}；状态：{execution['run_status']}"),
            TraceEvent(step=2, kind="evaluation", title="代码输出", detail=execution["stdout"] or execution["stderr"] or "程序未产生输出。", status=execution["run_status"]),
            TraceEvent(step=3, kind="reasoning", title="错误分析与复盘", detail=diagnosis.get("root_cause", "")),
        ]
        return SubmissionResult(run_id=str(uuid4()), language=request.language, **execution, diagnosis=diagnosis, trace=trace)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
