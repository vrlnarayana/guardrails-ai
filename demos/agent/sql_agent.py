import streamlit as st
from guardrails import Guard

from core.types import AgentResult, AgentStep
from core.llm import configure_openai

try:
    from guardrails.hub import DetectPII
    _PII_AVAILABLE = True
except ImportError:
    DetectPII = None
    _PII_AVAILABLE = False

try:
    from guardrails.hub import ValidSQL
    _SQL_AVAILABLE = True
except ImportError:
    ValidSQL = None
    _SQL_AVAILABLE = False

PII_INSTALL = "guardrails hub install hub://guardrails/detect_pii"
SQL_INSTALL = "guardrails hub install hub://guardrails/valid_sql"

DEFAULT_QUERY = "Show me all orders placed by john.smith@company.com in the last 30 days"

GUARD_CODE = """\
from guardrails.hub import DetectPII, ValidSQL
from guardrails import Guard

# Input guard — redact PII before sending to LLM (on_fail="fix" sanitises, not blocks)
pii_guard = Guard().use(DetectPII(
    pii_entities=["EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER"],
    on_fail="fix",
))
pii_result = pii_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": user_query}],
)
sanitised_query = pii_result.validated_output  # PII redacted, pipeline continues

# Output guard — validate the generated SQL
sql_guard = Guard().use(ValidSQL(on_fail="exception"))
sql_result = sql_guard(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": sql_system_prompt},
        {"role": "user", "content": sanitised_query},
    ],
)
# sql_result.validation_passed → True/False
# sql_result.validated_output  → valid SQL string
"""

SQL_SYSTEM_PROMPT = (
    "You are a SQL assistant. Convert the user's natural language query into a valid "
    "PostgreSQL SELECT statement. Respond with ONLY the SQL query, no explanation. "
    "Use the schema: orders(id, customer_id, status, created_at), "
    "customers(id, email, name)."
)


def run_agent(api_key: str, query: str, model: str) -> AgentResult:
    configure_openai(api_key)
    steps = []

    # ── Step 1: Input guard (PII check on user query) ─────────────────────────
    if not _PII_AVAILABLE:
        steps.append(AgentStep(
            name="Step 1: Input Guard",
            guard_name="DetectPII",
            passed=False,
            input_text=query,
            output_text="",
            error="Validator not installed.",
            install_hint=PII_INSTALL,
        ))
        return AgentResult(steps=steps, final_output="Cannot run: validators not installed.", blocked=True)

    try:
        pii_guard = Guard().use(DetectPII(
            pii_entities=["EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER"],
            on_fail="fix",
        ))
        pii_result = pii_guard(
            model=model,
            messages=[{"role": "user", "content": query}],
        )
        step1_passed = bool(pii_result.validation_passed)
        sanitised_query = str(pii_result.validated_output or query)
    except Exception as exc:
        step1_passed = False
        sanitised_query = query

    steps.append(AgentStep(
        name="Step 1: Input Guard",
        guard_name="DetectPII",
        passed=step1_passed,
        input_text=query,
        output_text=sanitised_query,
        error=None if step1_passed else "PII detected in query — sanitised before sending to LLM.",
        install_hint=None,
    ))

    # on_fail="fix" means PII is redacted, not blocked — pipeline continues with sanitised_query

    # ── Step 2: Output guard (SQL validation) ────────────────────────────────
    if not _SQL_AVAILABLE:
        steps.append(AgentStep(
            name="Step 2: Output Guard",
            guard_name="ValidSQL",
            passed=False,
            input_text=sanitised_query,
            output_text="",
            error="Validator not installed.",
            install_hint=SQL_INSTALL,
        ))
        return AgentResult(steps=steps, final_output="Cannot run: validators not installed.", blocked=True)

    try:
        sql_guard = Guard().use(ValidSQL(on_fail="exception"))
        sql_result = sql_guard(
            model=model,
            messages=[
                {"role": "system", "content": SQL_SYSTEM_PROMPT},
                {"role": "user", "content": sanitised_query},
            ],
        )
        step2_passed = bool(sql_result.validation_passed)
        generated_sql = str(sql_result.validated_output or sql_result.raw_llm_output or "")
    except Exception as exc:
        step2_passed = False
        generated_sql = str(exc)

    steps.append(AgentStep(
        name="Step 2: Output Guard",
        guard_name="ValidSQL",
        passed=step2_passed,
        input_text=sanitised_query,
        output_text=generated_sql,
        error=None if step2_passed else "Generated SQL failed validation.",
        install_hint=None,
    ))

    return AgentResult(
        steps=steps,
        final_output=generated_sql if step2_passed else "SQL generation failed validation.",
        blocked=not step2_passed,
    )


def render(api_key: str, model: str) -> None:
    st.subheader("🗄️ SQL Agent")
    st.caption(
        "PII guard sanitises the user query before it reaches the LLM. "
        "SQL validator ensures the generated query is syntactically valid before 'execution'."
    )

    col_in, col_out = st.columns([1, 1])

    with col_in:
        query = st.text_area(
            "Natural language query",
            value=DEFAULT_QUERY,
            height=120,
            key="sql_query",
            help="Try removing the email to see the PII guard pass.",
        )
        st.markdown("**Schema:** `orders(id, customer_id, status, created_at)`, `customers(id, email, name)`")
        run = st.button("▶ Run Agent", key="sql_run", type="primary")
        with st.expander("📋 Guard setup code"):
            st.code(GUARD_CODE, language="python")

    with col_out:
        if not api_key:
            st.warning("Enter your OpenAI API key in the sidebar.")
            return
        if run:
            with st.spinner("Running SQL agent pipeline…"):
                result = run_agent(api_key, query, model)
            _render_result(result)


def _render_result(result: AgentResult) -> None:
    st.markdown("**Pipeline trace:**")
    for step in result["steps"]:
        if step["install_hint"]:
            st.error(f"**{step['name']}** — {step['guard_name']}: not installed")
            st.code(step["install_hint"], language="bash")
        elif step["passed"]:
            detail = f" → `{step['output_text'][:60]}…`" if step["output_text"] and step["output_text"] != step["input_text"] else ""
            st.success(f"✅ **{step['name']}** — {step['guard_name']}: passed{detail}")
        else:
            st.error(f"❌ **{step['name']}** — {step['guard_name']}: {step['error']}")

    st.divider()
    if result["blocked"]:
        st.error("🚫 Pipeline blocked")
    else:
        st.success("✅ Valid SQL generated (simulated execution):")
        st.code(result["final_output"], language="sql")
