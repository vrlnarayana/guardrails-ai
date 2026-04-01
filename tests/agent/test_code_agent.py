from unittest.mock import MagicMock, patch
import demos.agent.code_agent as module


def _mock_injection_guard(is_injection: bool, reason: str = "test"):
    mock_result = MagicMock()
    mock_result.validated_output = {"is_injection": is_injection, "reason": reason}
    mock_guard = MagicMock()
    mock_guard.return_value = mock_result
    return mock_guard


def _mock_guard(passed: bool, raw: str = "def hello(): return 'hi'"):
    mock_result = MagicMock()
    mock_result.validation_passed = passed
    mock_result.validated_output = raw if passed else ""
    mock_result.raw_llm_output = raw
    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.return_value = mock_result
    mock_guard.validate.return_value = mock_result
    return mock_guard


def test_clean_code_passes_all_steps(monkeypatch):
    monkeypatch.setattr(module, "_SECRETS_AVAILABLE", True)
    monkeypatch.setattr(module, "_PYTHON_AVAILABLE", True)
    injection_guard = _mock_injection_guard(is_injection=False)
    output_guard = _mock_guard(True, "def add(a, b): return a + b")

    with patch("demos.agent.code_agent.Guard") as MockGuard, \
         patch("demos.agent.code_agent.SecretsPresent"), \
         patch("demos.agent.code_agent.ValidPython"), \
         patch("demos.agent.code_agent.configure_openai") as mock_configure:
        MockGuard.for_pydantic.return_value = injection_guard
        MockGuard.return_value = output_guard
        result = module.run_agent("sk-test", "Write an add function", "gpt-4o-mini")

    assert result["blocked"] is False
    assert len(result["steps"]) == 3
    mock_configure.assert_called_once_with("sk-test")


def test_code_with_secret_blocked(monkeypatch):
    monkeypatch.setattr(module, "_SECRETS_AVAILABLE", True)
    monkeypatch.setattr(module, "_PYTHON_AVAILABLE", True)
    injection_guard = _mock_injection_guard(is_injection=False)
    secrets_guard = _mock_guard(False, "AWS_SECRET='abc123'")

    with patch("demos.agent.code_agent.Guard") as MockGuard, \
         patch("demos.agent.code_agent.SecretsPresent"), \
         patch("demos.agent.code_agent.ValidPython"), \
         patch("demos.agent.code_agent.configure_openai"):
        MockGuard.for_pydantic.return_value = injection_guard
        MockGuard.return_value = secrets_guard
        result = module.run_agent("sk-test", "Write code with hardcoded creds", "gpt-4o-mini")

    assert result["blocked"] is True
    assert len(result["steps"]) == 2


def test_validators_missing(monkeypatch):
    monkeypatch.setattr(module, "_SECRETS_AVAILABLE", False)
    monkeypatch.setattr(module, "_PYTHON_AVAILABLE", False)
    injection_guard = _mock_injection_guard(is_injection=False)

    with patch("demos.agent.code_agent.Guard") as MockGuard, \
         patch("demos.agent.code_agent.configure_openai"):
        MockGuard.for_pydantic.return_value = injection_guard
        result = module.run_agent("sk-test", "write code", "gpt-4o-mini")

    assert result["blocked"] is True
    assert result["steps"][1]["install_hint"] is not None
