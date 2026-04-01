import pytest
from unittest.mock import MagicMock, patch
import demos.prompt.pii_detection as module


def _make_mock_guard(passed: bool, validated: str, raw: str):
    mock_result = MagicMock()
    mock_result.validation_passed = passed
    mock_result.validated_output = validated
    mock_result.raw_llm_output = raw

    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.return_value = mock_result
    return mock_guard


def test_run_guard_pii_detected(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", True)
    mock_guard = _make_mock_guard(
        passed=False,
        validated="Hello, [PERSON]. Email: [EMAIL_ADDRESS]",
        raw="Hello, John Smith. Email: john@example.com",
    )
    with patch("demos.prompt.pii_detection.Guard") as MockGuard, \
         patch("demos.prompt.pii_detection.DetectPII"):
        MockGuard.return_value = mock_guard
        result = module.run_guard("sk-test", "My name is John", "gpt-4o-mini")

    assert result["passed"] is False
    assert "[PERSON]" in result["output"]
    assert "john@example.com" in result["raw_output"]
    assert result["error"] is None
    assert result["install_hint"] is None


def test_run_guard_no_pii(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", True)
    mock_guard = _make_mock_guard(
        passed=True,
        validated="GDPR protects personal data in the EU.",
        raw="GDPR protects personal data in the EU.",
    )
    with patch("demos.prompt.pii_detection.Guard") as MockGuard, \
         patch("demos.prompt.pii_detection.DetectPII"), \
         patch("demos.prompt.pii_detection.configure_openai") as mock_configure:
        MockGuard.return_value = mock_guard
        result = module.run_guard("sk-test", "What is GDPR?", "gpt-4o-mini")

    assert result["passed"] is True
    assert result["error"] is None
    mock_configure.assert_called_once_with("sk-test")


def test_run_guard_validator_not_installed(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", False)
    result = module.run_guard("sk-test", "anything", "gpt-4o-mini")

    assert result["passed"] is False
    assert result["install_hint"] == module.INSTALL_CMD


def test_run_guard_api_error(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", True)
    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.side_effect = Exception("401 Unauthorized")
    with patch("demos.prompt.pii_detection.Guard") as MockGuard, \
         patch("demos.prompt.pii_detection.DetectPII"):
        MockGuard.return_value = mock_guard
        result = module.run_guard("bad-key", "hello", "gpt-4o-mini")

    assert result["passed"] is False
    assert "401" in result["error"]
