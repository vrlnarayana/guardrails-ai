# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is
A Streamlit demo app showcasing Guardrails AI validators in prompt-based and agent-based LLM workflows.

## Running the App
```bash
pip install -r requirements.txt
guardrails hub install hub://guardrails/detect_pii
guardrails hub install hub://sainatha/prompt_injection_detector
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/provenance_llm
guardrails hub install hub://guardrails/valid_sql
guardrails hub install hub://guardrails/secrets_present
guardrails hub install hub://reflex/valid_python
streamlit run app.py
```

## Running Tests

Requires Python 3.11+ (`guardrails-ai` does not support Python 3.7):
```bash
python3.11 -m pytest tests/ -v
python3.11 -m pytest tests/prompt/test_pii_detection.py -v   # single test file
```

## Architecture
- `app.py` — entry point, sidebar, delegates to `tabs/`
- `tabs/` — tab-level routing only, no business logic
- `demos/` — each demo owns its guard logic + Streamlit UI via `render(api_key, model)`
- `core/` — shared types (`GuardResult`, `AgentResult`) and OpenAI config

## Key Patterns

### Prompt demos (`demos/prompt/`)
Each module exposes:
- `_VALIDATOR_AVAILABLE: bool` — False if hub validator not installed (set at import time)
- `INSTALL_CMD: str` — hub install command to show the user
- `GUARD_CODE: str` — example code shown in the UI expander
- `build_guard() -> Guard` — creates the configured guard
- `run_guard(api_key, prompt, model) -> GuardResult` — runs guard, never raises
- `render(api_key, model) -> None` — Streamlit UI for this demo

### Agent demos (`demos/agent/`)
Each module exposes:
- `_INJECTION_AVAILABLE: bool` (or `_PII_AVAILABLE` etc.) — per-validator availability flags
- `GUARD_CODE: str` — example pipeline code shown in the UI expander
- `run_agent(api_key, query, model) -> AgentResult` — runs pipeline, never raises
- `render(api_key, model) -> None` — Streamlit UI with step-trace display

### Shared types (`core/types.py`)
```python
class GuardResult(TypedDict):
    passed: bool
    output: str
    raw_output: str
    error: Optional[str]
    install_hint: Optional[str]

class AgentStep(TypedDict):
    name: str
    guard_name: str
    passed: bool
    input_text: str
    output_text: str
    error: Optional[str]
    install_hint: Optional[str]

class AgentResult(TypedDict):
    steps: List[AgentStep]
    final_output: str
    blocked: bool
```

### configure_openai call order
`configure_openai(api_key)` must be called **after** the `_VALIDATOR_AVAILABLE` check — never as the first line. If validators are missing, return early without touching the environment.

## Validator Import Pattern
Validators are imported at module level inside a try/except to gracefully handle missing installs:
```python
try:
    from guardrails.hub import DetectPII
    _VALIDATOR_AVAILABLE = True
except ImportError:
    DetectPII = None
    _VALIDATOR_AVAILABLE = False
```

## Hub Validator Package Names
The actual hub package names differ from the class names used in code:

| Class | Hub package |
|-------|-------------|
| `DetectPII` | `hub://guardrails/detect_pii` |
| `PromptInjectionDetector` | `hub://sainatha/prompt_injection_detector` |
| `ToxicLanguage` | `hub://guardrails/toxic_language` |
| `ProvenanceLLM` | `hub://guardrails/provenance_llm` |
| `ValidSQL` | `hub://guardrails/valid_sql` |
| `SecretsPresent` | `hub://guardrails/secrets_present` |
| `ValidPython` | `hub://reflex/valid_python` |
