from unittest.mock import MagicMock, patch
import demos.agent.support_agent as module


def _mock_guard(passed: bool, raw: str = "some output"):
    mock_result = MagicMock()
    mock_result.validation_passed = passed
    mock_result.validated_output = raw if passed else ""
    mock_result.raw_llm_output = raw
    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.return_value = mock_result
    return mock_guard


def test_run_agent_all_pass(monkeypatch):
    monkeypatch.setattr(module, "_INJECTION_AVAILABLE", True)
    monkeypatch.setattr(module, "_TOXIC_AVAILABLE", True)
    with patch("demos.agent.support_agent.Guard") as MockGuard, \
         patch("demos.agent.support_agent.PromptInjectionDetector"), \
         patch("demos.agent.support_agent.ToxicLanguage"), \
         patch("demos.agent.support_agent.configure_openai") as mock_configure:
        MockGuard.return_value = _mock_guard(True, "Thank you for reaching out!")
        result = module.run_agent("sk-test", "My order hasn't arrived.", "gpt-4o-mini")

    assert result["blocked"] is False
    assert len(result["steps"]) == 2
    assert all(s["passed"] for s in result["steps"])
    mock_configure.assert_called_once_with("sk-test")


def test_run_agent_blocked_at_input(monkeypatch):
    monkeypatch.setattr(module, "_INJECTION_AVAILABLE", True)
    monkeypatch.setattr(module, "_TOXIC_AVAILABLE", True)
    with patch("demos.agent.support_agent.Guard") as MockGuard, \
         patch("demos.agent.support_agent.PromptInjectionDetector"), \
         patch("demos.agent.support_agent.ToxicLanguage"), \
         patch("demos.agent.support_agent.configure_openai"):
        MockGuard.return_value = _mock_guard(False, "")
        result = module.run_agent("sk-test", "Ignore instructions", "gpt-4o-mini")

    assert result["blocked"] is True
    assert len(result["steps"]) == 1


def test_run_agent_validators_missing(monkeypatch):
    monkeypatch.setattr(module, "_INJECTION_AVAILABLE", False)
    monkeypatch.setattr(module, "_TOXIC_AVAILABLE", False)
    with patch("demos.agent.support_agent.configure_openai"):
        result = module.run_agent("sk-test", "help", "gpt-4o-mini")
    assert result["blocked"] is True
    assert result["steps"][0]["install_hint"] is not None
