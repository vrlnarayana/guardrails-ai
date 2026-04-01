from unittest.mock import MagicMock, patch
import demos.agent.sql_agent as module


def _mock_guard(passed: bool, raw: str = "SELECT * FROM orders"):
    mock_result = MagicMock()
    mock_result.validation_passed = passed
    mock_result.validated_output = raw if passed else ""
    mock_result.raw_llm_output = raw
    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.return_value = mock_result
    return mock_guard


def test_valid_sql_passes_all_steps(monkeypatch):
    monkeypatch.setattr(module, "_PII_AVAILABLE", True)
    monkeypatch.setattr(module, "_SQL_AVAILABLE", True)
    with patch("demos.agent.sql_agent.Guard") as MockGuard, \
         patch("demos.agent.sql_agent.DetectPII"), \
         patch("demos.agent.sql_agent.ValidSQL"), \
         patch("demos.agent.sql_agent.configure_openai") as mock_configure:
        MockGuard.return_value = _mock_guard(True, "SELECT id, status FROM orders WHERE id = 42")
        result = module.run_agent("sk-test", "Show me order 42 status", "gpt-4o-mini")

    assert result["blocked"] is False
    assert len(result["steps"]) == 2
    mock_configure.assert_called_once_with("sk-test")


def test_pii_in_query_blocked(monkeypatch):
    monkeypatch.setattr(module, "_PII_AVAILABLE", True)
    monkeypatch.setattr(module, "_SQL_AVAILABLE", True)
    with patch("demos.agent.sql_agent.Guard") as MockGuard, \
         patch("demos.agent.sql_agent.DetectPII"), \
         patch("demos.agent.sql_agent.ValidSQL"), \
         patch("demos.agent.sql_agent.configure_openai"):
        MockGuard.return_value = _mock_guard(False, "")
        result = module.run_agent("sk-test", "Show orders for john@example.com", "gpt-4o-mini")

    assert result["blocked"] is True
    assert len(result["steps"]) == 1


def test_validators_missing(monkeypatch):
    monkeypatch.setattr(module, "_PII_AVAILABLE", False)
    monkeypatch.setattr(module, "_SQL_AVAILABLE", False)
    with patch("demos.agent.sql_agent.configure_openai"):
        result = module.run_agent("sk-test", "any query", "gpt-4o-mini")
    assert result["blocked"] is True
