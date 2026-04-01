from unittest.mock import MagicMock, patch
import demos.prompt.toxic_filter as module


def _make_mock_guard(passed: bool, validated: str, raw: str):
    mock_result = MagicMock()
    mock_result.validation_passed = passed
    mock_result.validated_output = validated
    mock_result.raw_llm_output = raw
    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.return_value = mock_result
    return mock_guard


def test_toxic_output_blocked(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", True)
    mock_guard = _make_mock_guard(passed=False, validated="", raw="You're an idiot for asking that.")
    with patch("demos.prompt.toxic_filter.Guard") as MockGuard, \
         patch("demos.prompt.toxic_filter.ToxicLanguage"), \
         patch("demos.prompt.toxic_filter.configure_openai"):
        MockGuard.return_value = mock_guard
        result = module.run_guard("sk-test", "Tell me I'm stupid", "gpt-4o-mini")

    assert result["passed"] is False
    assert "idiot" in result["raw_output"]


def test_safe_output_passes(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", True)
    mock_guard = _make_mock_guard(passed=True, validated="That's a great question!", raw="That's a great question!")
    with patch("demos.prompt.toxic_filter.Guard") as MockGuard, \
         patch("demos.prompt.toxic_filter.ToxicLanguage"), \
         patch("demos.prompt.toxic_filter.configure_openai") as mock_configure:
        MockGuard.return_value = mock_guard
        result = module.run_guard("sk-test", "Am I doing well?", "gpt-4o-mini")

    assert result["passed"] is True
    mock_configure.assert_called_once_with("sk-test")


def test_validator_not_installed(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", False)
    result = module.run_guard("sk-test", "anything", "gpt-4o-mini")
    assert result["install_hint"] == module.INSTALL_CMD
