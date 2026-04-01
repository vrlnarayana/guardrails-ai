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


def test_pii_detected_sanitises_and_continues(monkeypatch):
    """on_fail='fix' means PII is redacted and the pipeline continues — not blocked at step 1."""
    monkeypatch.setattr(module, "_PII_AVAILABLE", True)
    monkeypatch.setattr(module, "_SQL_AVAILABLE", True)

    pii_guard = _mock_guard(False, "sanitised query")
    sql_guard = _mock_guard(True, "SELECT * FROM orders")

    with patch("demos.agent.sql_agent.Guard") as MockGuard, \
         patch("demos.agent.sql_agent.DetectPII"), \
         patch("demos.agent.sql_agent.ValidSQL"), \
         patch("demos.agent.sql_agent.configure_openai"):
        MockGuard.side_effect = [pii_guard, sql_guard]
        result = module.run_agent("sk-test", "Show orders for john@example.com", "gpt-4o-mini")

    # Pipeline must NOT be blocked — PII fixed and pipeline continues
    assert result["blocked"] is False
    assert len(result["steps"]) == 2
    assert result["steps"][0]["passed"] is False  # PII was detected (step shows warning)
    assert result["steps"][0]["install_hint"] is None  # not a missing-validator error


def test_validators_missing(monkeypatch):
    monkeypatch.setattr(module, "_PII_AVAILABLE", False)
    monkeypatch.setattr(module, "_SQL_AVAILABLE", False)
    with patch("demos.agent.sql_agent.configure_openai"):
        result = module.run_agent("sk-test", "any query", "gpt-4o-mini")
    assert result["blocked"] is True
