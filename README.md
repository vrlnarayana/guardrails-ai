# Guardrails AI Demo App

An interactive Streamlit app that demonstrates how [Guardrails AI](https://github.com/guardrails-ai/guardrails) can be used to add safety and validation layers to LLM-powered applications — both simple prompt calls and multi-step agent pipelines.

## What It Shows

### Prompt Guards (5 demos)
Each demo wraps an OpenAI call with a single validator and shows the raw vs. guarded output side by side.

| Demo | Validator | What it teaches |
|------|-----------|-----------------|
| PII Detection | `DetectPII` | Redacts names, emails, phone numbers from LLM responses |
| Prompt Injection | `Guard.for_pydantic(InjectionCheck)` | LLM classifier blocks adversarial inputs |
| Toxic Filter | `ToxicLanguage` | Catches hostile or unsafe output post-generation |
| Structured Output | `Guard.for_pydantic()` | Enforces JSON schema compliance on LLM responses |
| Factuality | `ProvenanceLLM` | Detects hallucinations relative to a seeded source document |

### Agent Guards (4 scenarios)
Each scenario shows a multi-step pipeline with guards firing at input and output stages, rendering a visible step-by-step trace with pass/fail badges.

| Scenario | Input Guard | Output Guard |
|----------|-------------|--------------|
| Customer Support Bot | LLM Injection Classifier | Toxic Language |
| SQL Agent | PII Detection (sanitise) | Valid SQL |
| Research Summariser | LLM Injection Classifier | Provenance LLM |
| Code Generator | LLM Injection Classifier | Secrets Present + Valid Python |

---

## Quickstart

### Prerequisites
- Python 3.11+
- An OpenAI API key
- A [Guardrails AI account](https://hub.guardrailsai.com) (free) — run `guardrails configure` after installing

### Setup

```bash
# 1. Create a virtual environment (required — guardrails hub install uses uv internally)
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Authenticate with Guardrails Hub
guardrails configure

# 4. Install hub validators
guardrails hub install hub://guardrails/detect_pii
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/provenance_llm
guardrails hub install hub://guardrails/valid_sql
guardrails hub install hub://guardrails/secrets_present
guardrails hub install hub://reflex/valid_python

# 5. Run the app (must be inside the venv)
streamlit run app.py
```

Enter your OpenAI API key in the sidebar. All demos run against `gpt-4o-mini` by default (switchable to `gpt-4o`).

> **Note:** If `toxic_language` or `provenance_llm` post-install scripts fail with a PyTorch error, the packages are still installed. Manually add them to `.guardrails/hub_registry.json` — see [Known Issues](#known-issues).

---

## Project Structure

```
guardrails-ai/
├── app.py                        # Entry point — sidebar, top-level tabs
├── tabs/
│   ├── prompt_guards.py          # Routes to the 5 prompt demo sub-tabs
│   └── agent_guards.py           # Scenario selector + routes to agent demos
├── demos/
│   ├── prompt/
│   │   ├── pii_detection.py
│   │   ├── prompt_injection.py   # LLM-based injection classifier (no hub validator)
│   │   ├── toxic_filter.py
│   │   ├── structured_output.py
│   │   └── factuality.py
│   └── agent/
│       ├── support_agent.py
│       ├── sql_agent.py
│       ├── research_agent.py
│       └── code_agent.py
├── core/
│   ├── types.py                  # GuardResult, AgentResult, AgentStep TypedDicts
│   └── llm.py                    # configure_openai(api_key)
├── .guardrails/
│   └── hub_registry.json         # Registered hub validators (project-scoped)
├── tests/                        # 34 unit tests (pytest)
└── requirements.txt
```

Each module in `demos/` owns both its guard logic and its Streamlit UI. Tabs contain no business logic — they only route to `render()`.

---

## Running Tests

```bash
source .venv/bin/activate
python3.11 -m pytest tests/ -v
```

34 tests, no external dependencies required (all validators are mocked).

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit>=1.32` | UI framework |
| `guardrails-ai>=0.5` | Guard framework + hub validators |
| `openai>=1.0` | LLM calls |
| `pydantic>=2.0` | Structured output schema |
| `python-dotenv>=1.0` | Optional `.env` file support |

Optionally set `OPENAI_API_KEY` in a `.env` file (sidebar input takes precedence).

---

## Known Issues

### PyTorch/NumPy version conflict
`hub://guardrails/toxic_language` and `hub://guardrails/provenance_llm` post-install scripts may fail with:
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x
```
Fix: downgrade NumPy and/or transformers, then manually register the validators:
```bash
pip install "numpy<2.0" "transformers<4.50"
```
Then add the validators to `.guardrails/hub_registry.json` manually (see the file for the existing entry format).

### hub://sainatha/prompt_injection_detector not available
This package is not published in the Guardrails hub registry. The Prompt Injection demo instead uses `Guard.for_pydantic()` with an LLM-based `InjectionCheck` classifier — no hub install needed.

### guardrails hub install requires a virtual environment
`guardrails hub install` uses `uv` internally and will fail outside a venv with:
```
error: No virtual environment found; run `uv venv` to create an environment
```
Always run installs from within `.venv`.
