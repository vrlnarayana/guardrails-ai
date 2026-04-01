import json
from unittest.mock import MagicMock, patch
import demos.prompt.structured_output as module


def test_run_guard_returns_parsed_model(monkeypatch):
    mock_result = MagicMock()
    mock_result.validation_passed = True
    mock_result.validated_output = {"rating": 4, "summary": "Good product.", "pros": ["Fast", "Reliable"]}
    mock_result.raw_llm_output = '{"rating": 4, "summary": "Good product.", "pros": ["Fast", "Reliable"]}'

    mock_guard = MagicMock()
    mock_guard.return_value = mock_result

    with patch("demos.prompt.structured_output.Guard") as MockGuard, \
         patch("demos.prompt.structured_output.configure_openai") as mock_configure:
        MockGuard.for_pydantic.return_value = mock_guard
        result = module.run_guard("sk-test", "Review this laptop", "gpt-4o-mini")

    assert result["passed"] is True
    assert "rating" in result["output"]
    mock_configure.assert_called_once_with("sk-test")


def test_run_guard_schema_violation(monkeypatch):
    mock_result = MagicMock()
    mock_result.validation_passed = False
    mock_result.validated_output = None
    mock_result.raw_llm_output = "It was pretty good overall."

    mock_guard = MagicMock()
    mock_guard.return_value = mock_result

    with patch("demos.prompt.structured_output.Guard") as MockGuard, \
         patch("demos.prompt.structured_output.configure_openai"):
        MockGuard.for_pydantic.return_value = mock_guard
        result = module.run_guard("sk-test", "Review this laptop", "gpt-4o-mini")

    assert result["passed"] is False
    assert "pretty good" in result["raw_output"]


def test_run_guard_api_error(monkeypatch):
    mock_guard = MagicMock()
    mock_guard.side_effect = Exception("Rate limit exceeded")
    with patch("demos.prompt.structured_output.Guard") as MockGuard, \
         patch("demos.prompt.structured_output.configure_openai"):
        MockGuard.for_pydantic.return_value = mock_guard
        result = module.run_guard("sk-test", "Review this laptop", "gpt-4o-mini")

    assert result["passed"] is False
    assert "Rate limit" in result["error"]
