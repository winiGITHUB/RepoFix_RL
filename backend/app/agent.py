from dataclasses import dataclass


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
