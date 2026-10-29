from dataclasses import dataclass

from .models import TaskSummary


@dataclass(frozen=True)
class DemoTask:
    summary: TaskSummary
    files: dict[str, str]
    test_file: str


TASKS: dict[str, DemoTask] = {
    "string-normalize": DemoTask(
        summary=TaskSummary(
            id="string-normalize",
            title="修复字符串规范化中的空白处理",
            description="normalize_name 应去掉首尾空白，并将连续空格压缩为一个下划线。当前实现只替换了第一个空格。",
            difficulty="入门",
            language="Python",
        ),
        files={
            "solution.py": 'def normalize_name(value: str) -> str:\n    """Normalize a display name for use as a slug."""\n    return value.strip().replace(" ", "_", 1).lower()\n',
        },
        test_file=(
            "from solution import normalize_name\n\n"
            "def test_trims_and_replaces_spaces():\n"
            "    assert normalize_name('  Ada Lovelace  ') == 'ada_lovelace'\n\n"
            "def test_collapses_repeated_spaces():\n"
            "    assert normalize_name('Grace   Hopper') == 'grace_hopper'\n\n"
            "def test_lowercases():\n"
            "    assert normalize_name('ALAN TURING') == 'alan_turing'\n"
        ),
    )
}


def list_tasks() -> list[TaskSummary]:
    return [task.summary for task in TASKS.values()]


def get_task(task_id: str) -> DemoTask:
    try:
        return TASKS[task_id]
    except KeyError as exc:
        raise ValueError(f"Unknown task: {task_id}") from exc
