from app.agent import DemoAgent
from app.evaluator import evaluate
from app.tasks import get_task


def test_demo_agent_repairs_string_normalization_task():
    result = evaluate(get_task("string-normalize"), DemoAgent(), "test-run")
    assert result.status == "passed"
    assert result.tests_passed == result.tests_total == 3
    assert result.score == 1.0
    assert "re.sub" in result.diff
    assert result.trace[-1].kind == "evaluation"
