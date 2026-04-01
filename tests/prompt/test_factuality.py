from unittest.mock import MagicMock, patch
import demos.prompt.factuality as module


def _make_mock_guard(passed: bool, validated: str, raw: str):
    mock_result = MagicMock()
    mock_result.validation_passed = passed
    mock_result.validated_output = validated
    mock_result.raw_llm_output = raw
    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.return_value = mock_result
    return mock_guard


def test_grounded_output_passes(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", True)
    mock_guard = _make_mock_guard(
        passed=True,
        validated="The Eiffel Tower is in Paris.",
        raw="The Eiffel Tower is in Paris.",
    )
    with patch("demos.prompt.factuality.Guard") as MockGuard, \
         patch("demos.prompt.factuality.ProvenanceLLM"), \
         patch("demos.prompt.factuality.configure_openai") as mock_configure:
        MockGuard.return_value = mock_guard
        result = module.run_guard("sk-test", "Where is the Eiffel Tower?", "gpt-4o-mini")

    assert result["passed"] is True
    mock_configure.assert_called_once_with("sk-test")


def test_hallucination_blocked(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", True)
    mock_guard = _make_mock_guard(
        passed=False,
        validated="",
        raw="The Eiffel Tower is in Berlin.",
    )
    with patch("demos.prompt.factuality.Guard") as MockGuard, \
         patch("demos.prompt.factuality.ProvenanceLLM"), \
         patch("demos.prompt.factuality.configure_openai"):
        MockGuard.return_value = mock_guard
        result = module.run_guard("sk-test", "Where is the Eiffel Tower?", "gpt-4o-mini")

    assert result["passed"] is False
    assert "Berlin" in result["raw_output"]


def test_validator_not_installed(monkeypatch):
    monkeypatch.setattr(module, "_VALIDATOR_AVAILABLE", False)
    result = module.run_guard("sk-test", "anything", "gpt-4o-mini")
    assert result["install_hint"] == module.INSTALL_CMD
