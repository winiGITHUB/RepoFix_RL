from typing import Literal

from pydantic import BaseModel, Field


class TaskSummary(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    language: str


class RunRequest(BaseModel):
    problem: str = Field(min_length=10, max_length=12000)
    language: Literal["python"]
    source_code: str = Field(min_length=1, max_length=30000)
    sample_input: str = Field(default="", max_length=4000)
    expected_output: str = Field(default="", max_length=4000)


class DiagnosisResult(BaseModel):
    verdict: str
    bug_category: str
    location: str
    counterexample: str
    root_cause: str
    hints: list[str]
    solution_review: str
    suggested_patch: str = ""


class SubmissionRequest(BaseModel):
    problem: str = Field(min_length=10, max_length=12000)
    language: Literal["python"]
    source_code: str = Field(min_length=1, max_length=30000)
    samples: list["SampleCase"] = Field(default_factory=list, max_length=20)


class SampleCase(BaseModel):
    input: str = Field(default="", max_length=4000)
    expected_output: str = Field(default="", max_length=4000)


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


class SubmissionResult(BaseModel):
    run_id: str
    language: str
    compile_status: str
    run_status: str
    stdout: str
    stderr: str
    duration_ms: int
    sample_results: list[dict]
    diagnosis: DiagnosisResult
    trace: list[TraceEvent]
