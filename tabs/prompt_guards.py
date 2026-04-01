import streamlit as st
from demos.prompt.pii_detection import render as render_pii
from demos.prompt.prompt_injection import render as render_injection
from demos.prompt.toxic_filter import render as render_toxic
from demos.prompt.structured_output import render as render_structured
from demos.prompt.factuality import render as render_factuality


def render(api_key: str, model: str) -> None:
    subtabs = st.tabs([
        "🔍 PII Detection",
        "💉 Prompt Injection",
        "🤬 Toxic Filter",
        "📐 Structured Output",
        "🔎 Factuality",
    ])

    with subtabs[0]:
        render_pii(api_key, model)
    with subtabs[1]:
        render_injection(api_key, model)
    with subtabs[2]:
        render_toxic(api_key, model)
    with subtabs[3]:
        render_structured(api_key, model)
    with subtabs[4]:
        render_factuality(api_key, model)
