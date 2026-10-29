from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import os

from .agent import DemoAgent, OpenAICompatibleAgent
from .evaluator import evaluate
from .models import RunRequest, RunResult, SubmissionResult, SubmissionRequest, TaskSummary, TraceEvent
from .submission_runner import run_submission
from .tasks import get_task, list_tasks

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
        return {"status": "ok", "provider": get_agent().name}
    except ValueError as exc:
        return {"status": "misconfigured", "provider": str(exc)}


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
        execution = run_submission(request.language, request.source_code, request.sample_input)
        diagnosis = get_agent().diagnose_submission(
            request.problem, request.language, request.source_code, execution
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
