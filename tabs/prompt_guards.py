import streamlit as st
from demos.prompt.pii_detection import render as render_pii


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
        st.info("Prompt Injection demo — coming in Task 5")
    with subtabs[2]:
        st.info("Toxic Filter demo — coming in Task 6")
    with subtabs[3]:
        st.info("Structured Output demo — coming in Task 7")
    with subtabs[4]:
        st.info("Factuality demo — coming in Task 8")
