from unittest.mock import MagicMock, patch
import demos.agent.support_agent as module


def _mock_injection_guard(is_injection: bool, reason: str = "test"):
    mock_result = MagicMock()
    mock_result.validated_output = {"is_injection": is_injection, "reason": reason}
    mock_guard = MagicMock()
    mock_guard.return_value = mock_result
    return mock_guard


def _mock_output_guard(passed: bool, output: str = "response"):
    mock_result = MagicMock()
    mock_result.validation_passed = passed
    mock_result.validated_output = output if passed else ""
    mock_result.raw_llm_output = output
    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.return_value = mock_result
    return mock_guard


def test_run_agent_all_pass(monkeypatch):
    monkeypatch.setattr(module, "_TOXIC_AVAILABLE", True)
    injection_guard = _mock_injection_guard(is_injection=False)
    output_guard = _mock_output_guard(passed=True, output="Thank you for reaching out!")

    with patch("demos.agent.support_agent.Guard") as MockGuard, \
         patch("demos.agent.support_agent.ToxicLanguage"), \
         patch("demos.agent.support_agent.configure_openai") as mock_configure:
        MockGuard.for_pydantic.return_value = injection_guard
        MockGuard.return_value = output_guard
        result = module.run_agent("sk-test", "My order hasn't arrived.", "gpt-4o-mini")

    assert result["blocked"] is False
    assert len(result["steps"]) == 2
    assert all(s["passed"] for s in result["steps"])
    mock_configure.assert_called_once_with("sk-test")


def test_run_agent_blocked_at_input(monkeypatch):
    monkeypatch.setattr(module, "_TOXIC_AVAILABLE", True)
    injection_guard = _mock_injection_guard(is_injection=True, reason="Attempts to hijack instructions")

    with patch("demos.agent.support_agent.Guard") as MockGuard, \
         patch("demos.agent.support_agent.ToxicLanguage"), \
         patch("demos.agent.support_agent.configure_openai"):
        MockGuard.for_pydantic.return_value = injection_guard
        result = module.run_agent("sk-test", "Ignore instructions", "gpt-4o-mini")

    assert result["blocked"] is True
    assert len(result["steps"]) == 1
    assert result["steps"][0]["passed"] is False


def test_run_agent_validators_missing(monkeypatch):
    monkeypatch.setattr(module, "_TOXIC_AVAILABLE", False)
    injection_guard = _mock_injection_guard(is_injection=False)

    with patch("demos.agent.support_agent.Guard") as MockGuard, \
         patch("demos.agent.support_agent.configure_openai"):
        MockGuard.for_pydantic.return_value = injection_guard
        result = module.run_agent("sk-test", "help", "gpt-4o-mini")

    assert result["blocked"] is True
    assert result["steps"][1]["install_hint"] is not None
