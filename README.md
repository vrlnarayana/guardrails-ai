# Guardrails AI Demo App

An interactive Streamlit app that demonstrates how [Guardrails AI](https://github.com/guardrails-ai/guardrails) can be used to add safety and validation layers to LLM-powered applications — both simple prompt calls and multi-step agent pipelines.

## What It Shows

### Prompt Guards (5 demos)
Each demo wraps an OpenAI call with a single validator and shows the raw vs. guarded output side by side.

| Demo | Validator | What it teaches |
|------|-----------|-----------------|
| PII Detection | `DetectPII` | Redacts names, emails, phone numbers from LLM responses |
| Prompt Injection | `PromptInjectionDetector` | Blocks adversarial inputs before they reach the LLM |
| Toxic Filter | `ToxicLanguage` | Catches hostile or unsafe output post-generation |
| Structured Output | `Guard.for_pydantic()` | Enforces JSON schema compliance on LLM responses |
| Factuality | `ProvenanceLLM` | Detects hallucinations relative to a seeded source document |

### Agent Guards (4 scenarios)
Each scenario shows a multi-step pipeline with guards firing at input and output stages, rendering a visible step-by-step trace with pass/fail badges.

| Scenario | Input Guard | Output Guard |
|----------|-------------|--------------|
| Customer Support Bot | Prompt Injection | Toxic Language |
| SQL Agent | PII Detection (sanitise) | Valid SQL |
| Research Summariser | Prompt Injection | Provenance LLM |
| Code Generator | Prompt Injection | Secrets Present + Valid Python |

---

## Quickstart

### Prerequisites
- Python 3.11+
- An OpenAI API key
- A [Guardrails AI account](https://hub.guardrailsai.com) (free) for hub validator installs

### Install

```bash
pip install -r requirements.txt
```

### Install hub validators

```bash
guardrails hub install hub://guardrails/detect_pii
guardrails hub install hub://sainatha/prompt_injection_detector
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/provenance_llm
guardrails hub install hub://guardrails/valid_sql
guardrails hub install hub://guardrails/secrets_present
guardrails hub install hub://reflex/valid_python
```

### Run

```bash
streamlit run app.py
```

Enter your OpenAI API key in the sidebar. All demos run against `gpt-4o-mini` by default (switchable to `gpt-4o`).

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
│   │   ├── prompt_injection.py
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
├── tests/                        # 35 unit tests (pytest)
└── requirements.txt
```

Each module in `demos/` owns both its guard logic and its Streamlit UI. Tabs contain no business logic — they only route to `render()`.

---

## Running Tests

```bash
python3.11 -m pytest tests/ -v
```

35 tests, no external dependencies required (all validators are mocked).

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
