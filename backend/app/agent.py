from dataclasses import dataclass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ProposedEdit:
    path: str
    content: str
    rationale: str


class DemoAgent:
    """Deterministic provider used to exercise the UI and evaluation loop.

    Replace this interface with a model-backed provider in a later milestone.
    """

    name = "demo-rule-provider"

    def diagnose_submission(self, problem: str, language: str, source_code: str, execution: dict) -> dict:
        return {
            "verdict": "需要结合题意与运行结果判断",
            "bug_category": "待分析",
            "location": "未配置真实模型诊断",
            "counterexample": execution.get("stderr", "请配置模型 Provider 生成针对性反例。"),
            "root_cause": "当前为演示 Provider，不能提供可靠代码诊断。",
            "hints": ["配置本地模型 Provider 后重新运行。"],
            "solution_review": "尚未生成复盘。",
            "suggested_patch": "",
        }

    def propose_edit(self, task_id: str, files: dict[str, str]) -> ProposedEdit:
        if task_id == "string-normalize":
            return ProposedEdit(
                path="solution.py",
                content=(
                    'import re\n\n'
                    'def normalize_name(value: str) -> str:\n'
                    '    """Normalize a display name for use as a slug."""\n'
                    '    return re.sub(r"\\s+", "_", value.strip()).lower()\n'
                ),
                rationale="用正则把一个或多个空白字符统一替换成单个下划线。",
            )
        raise ValueError(f"No demo policy is defined for task: {task_id}")


class OpenAICompatibleAgent:
    """Model-backed provider for OpenAI-compatible chat completion APIs.

    Configure MODEL_BASE_URL, MODEL_NAME, and optionally MODEL_API_KEY.
    The model must return one JSON object with path, content, and rationale.
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("MODEL_BASE_URL", "").rstrip("/")
        self.model = os.getenv("MODEL_NAME", "")
        self.api_key = os.getenv("MODEL_API_KEY", "")
        self.timeout = float(os.getenv("MODEL_TIMEOUT_SECONDS", "90"))
        if not self.base_url or not self.model:
            raise ValueError("Set MODEL_BASE_URL and MODEL_NAME to enable model mode")

    @property
    def name(self) -> str:
        return f"openai-compatible:{self.model}"

    def propose_edit(self, task_id: str, files: dict[str, str]) -> ProposedEdit:
        from .tasks import get_task

        task = get_task(task_id)
        system = (
            "You are a careful Python bug-fixing agent. Return exactly one JSON object, "
            'without markdown, with keys "path", "content", and "rationale". '
            "content must be the complete replacement file. Only edit a provided file."
        )
        user = json.dumps(
            {"task": task.summary.description, "files": files}, ensure_ascii=False
        )
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            f"{self.base_url}/chat/completions", data=payload, headers=headers
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"Model request failed: {exc}") from exc
        try:
            content = body["choices"][0]["message"]["content"]
            result = json.loads(content)
            path = str(result["path"])
            if path not in files:
                raise ValueError("Model selected a file outside the task workspace")
            return ProposedEdit(
                path=path,
                content=str(result["content"]),
                rationale=str(result.get("rationale", "模型未提供说明。")),
            )
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Model returned an invalid edit JSON response") from exc

    def diagnose_submission(self, problem: str, language: str, source_code: str, execution: dict) -> dict:
        system = (
            "你是循序渐进的算法代码诊断导师。根据题意、用户代码和真实运行结果诊断；"
            "不要默认代码错误。如果缺少完整测试，只能说当前样例下观察到什么，不可声称已通过隐藏测试。"
            "若 execution.compile_status 为 failed、timeout 或 unavailable，程序尚未运行；只能诊断编译器状态与 stderr，"
            "不得把原因归结为 stdin 输入格式，也不得声称观察到程序运行行为。"
            "输出严格 JSON，字段 verdict, bug_category, location, counterexample, root_cause, hints (array), solution_review, suggested_patch。"
            "先给提示，不要主动泄露完整解答；suggested_patch 可为空。"
        )
        user = json.dumps({"problem": problem, "language": language, "source_code": source_code, "execution": execution}, ensure_ascii=False)
        payload = json.dumps({"model": self.model, "temperature": 0.2, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "response_format": {"type": "json_object"}}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(f"{self.base_url}/chat/completions", data=payload, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            result = json.loads(content)
            return {key: result.get(key, "") for key in ("verdict", "bug_category", "location", "counterexample", "root_cause", "hints", "solution_review", "suggested_patch")}
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Model diagnosis failed: {exc}") from exc
