import streamlit as st

from demos.agent.support_agent import render as render_support
from demos.agent.sql_agent import render as render_sql
from demos.agent.research_agent import render as render_research
from demos.agent.code_agent import render as render_code

SCENARIOS = [
    "🤝 Customer Support Bot",
    "🗄️ SQL Agent",
    "📰 Research Summariser",
    "💻 Code Generator",
]


def render(api_key: str, model: str) -> None:
    scenario = st.selectbox("Choose agent scenario", SCENARIOS, key="agent_scenario")
    st.divider()

    if scenario == "🤝 Customer Support Bot":
        render_support(api_key, model)
    elif scenario == "🗄️ SQL Agent":
        render_sql(api_key, model)
    elif scenario == "📰 Research Summariser":
        render_research(api_key, model)
    elif scenario == "💻 Code Generator":
        render_code(api_key, model)
