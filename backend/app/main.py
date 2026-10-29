from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil

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
        compiler = os.getenv("CPP_COMPILER", "g++")
        return {
            "status": "ok",
            "provider": get_agent().name,
            "cpp_compiler": compiler,
            "cpp_compiler_found": str(shutil.which(compiler) is not None).lower(),
        }
    except ValueError as exc:
        compiler = os.getenv("CPP_COMPILER", "g++")
        return {
            "status": "misconfigured",
            "provider": str(exc),
            "cpp_compiler": compiler,
            "cpp_compiler_found": str(shutil.which(compiler) is not None).lower(),
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
            # A model must not reinterpret a compiler failure as a runtime/input bug.
            compiler_output = execution["stderr"].strip()
            if execution["compile_status"] == "failed" and "[compiler returned no diagnostic output]" in compiler_output:
                root_cause = "编译器返回失败状态，但没有提供错误信息；程序尚未运行，因此目前无法判断代码或输入格式是否有问题。"
                hints = [
                    "在终端运行 `C:\\msys64\\ucrt64\\bin\\g++.exe --version`，确认编译器可正常启动。",
                    "将 PROGRAM OUTPUT 中显示的完整编译命令复制到终端运行，并检查是否有安全软件拦截或进程异常退出。",
                    "如果问题持续，请提供完整的 PROGRAM OUTPUT 和后端终端日志。",
                ]
            else:
                root_cause = compiler_output or "编译器未能完成编译；程序尚未运行。"
                hints = ["根据下方 PROGRAM OUTPUT 中的编译器信息修正编译问题后再运行。"]
            diagnosis = {
                "verdict": "编译未通过，程序尚未运行。",
                "bug_category": "compiler",
                "location": "编译阶段",
                "counterexample": "无；样例尚未执行。",
                "root_cause": root_cause,
                "hints": hints,
                "solution_review": "由于编译失败，没有运行结果可用于评价算法逻辑或输入处理。",
                "suggested_patch": "",
            }
        else:
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
