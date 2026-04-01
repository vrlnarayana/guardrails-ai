import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

from tabs.prompt_guards import render as render_prompt_tab
from tabs.agent_guards import render as render_agent_tab

st.set_page_config(
    page_title="Guardrails AI Demo",
    page_icon="🛡️",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🛡️ Guardrails AI")
    st.caption("Demo Playground")

    api_key = st.text_input(
        "OpenAI API Key",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        placeholder="sk-...",
        help="Your key is used only for this session and never stored.",
    )

    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o"],
        index=0,
    )

    st.divider()
    st.markdown(
        """
**What is Guardrails AI?**

A Python framework that wraps your LLM calls with *validators* — pre-built checks
that detect and mitigate risks like PII leakage, prompt injection, toxic output,
and hallucinations. 70+ validators available on [Guardrails Hub](https://guardrailsai.com/hub).
        """
    )

# ── Main tabs ─────────────────────────────────────────────────────────────────
tab_prompt, tab_agent = st.tabs(["⚡ Prompt Guards", "🤖 Agent Guards"])

with tab_prompt:
    render_prompt_tab(api_key, model)

with tab_agent:
    render_agent_tab(api_key, model)
