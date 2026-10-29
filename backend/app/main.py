from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agent import DemoAgent
from .evaluator import evaluate
from .models import RunRequest, RunResult, TaskSummary
from .tasks import get_task, list_tasks

app = FastAPI(title="RepoFix-RL API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": DemoAgent.name}


@app.get("/api/tasks", response_model=list[TaskSummary])
def tasks() -> list[TaskSummary]:
    return list_tasks()


@app.post("/api/runs", response_model=RunResult)
def run_task(request: RunRequest) -> RunResult:
    try:
        task = get_task(request.task_id)
        return evaluate(task, DemoAgent(), run_id=str(uuid4()))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=408, detail="Evaluation timed out") from exc
