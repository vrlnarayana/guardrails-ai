from unittest.mock import MagicMock, patch
import demos.agent.code_agent as module


def _mock_guard(passed: bool, raw: str = "def hello(): return 'hi'"):
    mock_result = MagicMock()
    mock_result.validation_passed = passed
    mock_result.validated_output = raw if passed else ""
    mock_result.raw_llm_output = raw
    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.return_value = mock_result
    return mock_guard


def test_clean_code_passes_all_steps(monkeypatch):
    monkeypatch.setattr(module, "_INJECTION_AVAILABLE", True)
    monkeypatch.setattr(module, "_SECRETS_AVAILABLE", True)
    monkeypatch.setattr(module, "_PYTHON_AVAILABLE", True)
    with patch("demos.agent.code_agent.Guard") as MockGuard, \
         patch("demos.agent.code_agent.PromptInjectionDetector"), \
         patch("demos.agent.code_agent.SecretsPresent"), \
         patch("demos.agent.code_agent.ValidPython"), \
         patch("demos.agent.code_agent.configure_openai") as mock_configure:
        MockGuard.return_value = _mock_guard(True, "def add(a, b): return a + b")
        result = module.run_agent("sk-test", "Write an add function", "gpt-4o-mini")

    assert result["blocked"] is False
    assert len(result["steps"]) == 3
    mock_configure.assert_called_once_with("sk-test")


def test_code_with_secret_blocked(monkeypatch):
    monkeypatch.setattr(module, "_INJECTION_AVAILABLE", True)
    monkeypatch.setattr(module, "_SECRETS_AVAILABLE", True)
    monkeypatch.setattr(module, "_PYTHON_AVAILABLE", True)

    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        passed = call_count == 1  # First call (input guard) passes, second (secrets) fails
        mock_result = MagicMock()
        mock_result.validation_passed = passed
        mock_result.validated_output = "code" if passed else ""
        mock_result.raw_llm_output = "AWS_SECRET='abc123'"
        return mock_result

    mock_guard = MagicMock()
    mock_guard.use.return_value = mock_guard
    mock_guard.side_effect = side_effect

    with patch("demos.agent.code_agent.Guard") as MockGuard, \
         patch("demos.agent.code_agent.PromptInjectionDetector"), \
         patch("demos.agent.code_agent.SecretsPresent"), \
         patch("demos.agent.code_agent.ValidPython"), \
         patch("demos.agent.code_agent.configure_openai"):
        MockGuard.return_value = mock_guard
        result = module.run_agent("sk-test", "Write code with hardcoded creds", "gpt-4o-mini")

    assert result["blocked"] is True


def test_validators_missing(monkeypatch):
    monkeypatch.setattr(module, "_INJECTION_AVAILABLE", False)
    monkeypatch.setattr(module, "_SECRETS_AVAILABLE", False)
    monkeypatch.setattr(module, "_PYTHON_AVAILABLE", False)
    with patch("demos.agent.code_agent.configure_openai"):
        result = module.run_agent("sk-test", "write code", "gpt-4o-mini")
    assert result["blocked"] is True
    assert result["steps"][0]["install_hint"] is not None
