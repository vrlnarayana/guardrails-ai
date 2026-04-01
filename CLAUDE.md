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
Each demo module exposes:
- `_VALIDATOR_AVAILABLE: bool` — False if hub validator not installed (set at import time)
- `INSTALL_CMD: str` — hub install command to show the user
- `build_guard() -> Guard` — creates the configured guard
- `run_guard(api_key, prompt, model) -> GuardResult` — runs guard, never raises
- `render(api_key, model) -> None` — Streamlit UI for this demo

Agent demos expose `run_agent(api_key, query, model) -> AgentResult` instead of `run_guard`.

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
