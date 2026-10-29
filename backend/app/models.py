from pydantic import BaseModel


class TaskSummary(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    language: str


class RunRequest(BaseModel):
    task_id: str


class TraceEvent(BaseModel):
    step: int
    kind: str
    title: str
    detail: str
    status: str = "completed"


class RunResult(BaseModel):
    run_id: str
    task: TaskSummary
    status: str
    score: float
    tests_passed: int
    tests_total: int
    duration_ms: int
    summary: str
    diff: str
    trace: list[TraceEvent]
