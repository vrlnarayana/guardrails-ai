import streamlit as st

SCENARIOS = [
    "🤝 Customer Support Bot",
    "🗄️ SQL Agent",
    "📰 Research Summariser",
    "💻 Code Generator",
]


def render(api_key: str, model: str) -> None:
    scenario = st.selectbox("Choose agent scenario", SCENARIOS)
    st.info(f"{scenario} demo — coming in Tasks 9–12")
