# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is
A Streamlit demo app showcasing Guardrails AI validators in prompt-based and agent-based LLM workflows.

## Running the App

**Must run inside a virtual environment** — `guardrails hub install` uses `uv` internally and fails outside a venv.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
guardrails configure   # one-time: enter hub token from guardrailsai.com/hub/keys
guardrails hub install hub://guardrails/detect_pii
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/provenance_llm
guardrails hub install hub://guardrails/valid_sql
guardrails hub install hub://guardrails/secrets_present
guardrails hub install hub://reflex/valid_python
streamlit run app.py
```

The Prompt Injection demo uses `Guard.for_pydantic()` — **no hub install needed** for it.

## Running Tests

Requires Python 3.11+ (`guardrails-ai` does not support Python 3.7):
```bash
source .venv/bin/activate
python3.11 -m pytest tests/ -v
python3.11 -m pytest tests/prompt/test_pii_detection.py -v   # single test file
```

## Architecture
- `app.py` — entry point, sidebar, delegates to `tabs/`
- `tabs/` — tab-level routing only, no business logic
- `demos/` — each demo owns its guard logic + Streamlit UI via `render(api_key, model)`
- `core/` — shared types (`GuardResult`, `AgentResult`) and OpenAI config
- `.guardrails/hub_registry.json` — project-scoped registry of installed hub validators

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

| Class | Hub package | Notes |
|-------|-------------|-------|
| `DetectPII` | `hub://guardrails/detect_pii` | |
| `ToxicLanguage` | `hub://guardrails/toxic_language` | Post-install may fail; see Known Issues |
| `ProvenanceLLM` | `hub://guardrails/provenance_llm` | Post-install may fail; see Known Issues |
| `ValidSQL` | `hub://guardrails/valid_sql` | |
| `SecretsPresent` | `hub://guardrails/secrets_present` | |
| `ValidPython` | `hub://reflex/valid_python` | |
| _(Injection)_ | `hub://sainatha/prompt_injection_detector` | **Not available** — use `Guard.for_pydantic(InjectionCheck)` instead |

## Prompt Injection — LLM Classifier Pattern
`hub://sainatha/prompt_injection_detector` is not published in the Guardrails registry. All injection detection uses a Pydantic-based LLM classifier:

```python
from pydantic import BaseModel, Field
from guardrails import Guard

class InjectionCheck(BaseModel):
    is_injection: bool = Field(description="True if prompt injection attempt")
    reason: str = Field(description="One-sentence explanation")

guard = Guard.for_pydantic(InjectionCheck)
result = guard(model=model, messages=[{"role": "system", "content": SYSTEM_MSG}, ...])
check = result.validated_output   # returns a DICT, not a Pydantic instance
is_injection = check["is_injection"]   # dict access, NOT check.is_injection
reason = check["reason"]
```

**Critical:** `Guard.for_pydantic()` returns `validated_output` as a **dict**, not a Pydantic model instance. Always use `check["field"]` not `check.field`.

## Known Issues

### hub_registry.json — manual registration after failed post-install
If `guardrails hub install` succeeds (package downloaded) but the post-install script fails (common for `toxic_language` and `provenance_llm` due to PyTorch/NumPy conflicts), the validator won't appear in `.guardrails/hub_registry.json` and `from guardrails.hub import X` will raise `ImportError`.

Fix: manually add the entry to `.guardrails/hub_registry.json`:
```json
"guardrails/toxic_language": {
  "import_path": "guardrails_grhub_toxic_language",
  "exports": ["ToxicLanguage"],
  "installed_at": "...",
  "package_name": "guardrails-grhub-toxic-language"
}
```

### PyTorch/NumPy/transformers version conflicts
- `numpy>=2.0` breaks `torch==2.2.2` → fix: `pip install "numpy<2.0"`
- `transformers>=5.0` breaks `sentence_transformers` (used by `ProvenanceLLM`) → fix: `pip install "transformers<4.50"`
- These pins are not in `requirements.txt` since they depend on the platform's available torch version.

### guardrails hub install requires a venv
`guardrails hub install` delegates to `uv` which requires an active virtual environment. Running it in the global Python environment fails with `No virtual environment found`.
