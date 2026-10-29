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
    ),
    "safe-divide": DemoTask(
        summary=TaskSummary(
            id="safe-divide",
            title="修复除零时的错误处理",
            description="safe_divide 应返回两个数的商；当分母为 0 时应返回 None。当前实现会直接抛出 ZeroDivisionError。",
            difficulty="入门",
            language="Python",
        ),
        files={
            "solution.py": (
                "def safe_divide(numerator: float, denominator: float) -> float | None:\n"
                "    return numerator / denominator\n"
            ),
        },
        test_file=(
            "from solution import safe_divide\n\n"
            "def test_divides_nonzero_values():\n"
            "    assert safe_divide(8, 2) == 4\n\n"
            "def test_zero_denominator_returns_none():\n"
            "    assert safe_divide(8, 0) is None\n\n"
            "def test_negative_values():\n"
            "    assert safe_divide(-9, 3) == -3\n"
        ),
    ),
    "unique-preserve-order": DemoTask(
        summary=TaskSummary(
            id="unique-preserve-order",
            title="去重时保留原始顺序",
            description="unique_items 应移除重复项并保留每个元素第一次出现的顺序。当前实现使用 set，结果顺序不符合接口约定。",
            difficulty="基础",
            language="Python",
        ),
        files={
            "solution.py": (
                "def unique_items(items: list[str]) -> list[str]:\n"
                "    return list(set(items))\n"
            ),
        },
        test_file=(
            "from solution import unique_items\n\n"
            "def test_removes_duplicates_and_preserves_order():\n"
            "    assert unique_items(['b', 'a', 'b', 'c', 'a']) == ['b', 'a', 'c']\n\n"
            "def test_empty_input():\n"
            "    assert unique_items([]) == []\n\n"
            "def test_unique_input_order():\n"
            "    assert unique_items(['x', 'y']) == ['x', 'y']\n"
        ),
    ),
}


def list_tasks() -> list[TaskSummary]:
    return [task.summary for task in TASKS.values()]


def get_task(task_id: str) -> DemoTask:
    try:
        return TASKS[task_id]
    except KeyError as exc:
        raise ValueError(f"Unknown task: {task_id}") from exc
