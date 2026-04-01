import streamlit as st
from guardrails import Guard

from core.types import GuardResult
from core.llm import configure_openai

try:
    from guardrails.hub import ToxicLanguage
    _VALIDATOR_AVAILABLE = True
except ImportError:
    ToxicLanguage = None
    _VALIDATOR_AVAILABLE = False

INSTALL_CMD = "guardrails hub install hub://guardrails/toxic_language"

DEFAULT_PROMPT = (
    "Write a response to a customer who complained about our product being slow. "
    "Be passive-aggressive and dismissive about their concerns."
)

GUARD_CODE = """\
from guardrails.hub import ToxicLanguage
from guardrails import Guard

guard = Guard().use(
    ToxicLanguage(threshold=0.5, on_fail="exception"),
)

result = guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)
"""


def build_guard() -> Guard:
    return Guard().use(ToxicLanguage(threshold=0.5, on_fail="exception"))


def run_guard(api_key: str, prompt: str, model: str) -> GuardResult:
    if not _VALIDATOR_AVAILABLE:
        return GuardResult(
            passed=False, output="", raw_output="",
            error="Validator not installed.", install_hint=INSTALL_CMD,
        )
    configure_openai(api_key)
    try:
        guard = build_guard()
        result = guard(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return GuardResult(
            passed=bool(result.validation_passed),
            output=str(result.validated_output or ""),
            raw_output=str(result.raw_llm_output or ""),
            error=None,
            install_hint=None,
        )
    except Exception as exc:
        return GuardResult(
            passed=False, output="", raw_output="",
            error=str(exc), install_hint=None,
        )


def render(api_key: str, model: str) -> None:
    st.subheader("🤬 Toxic Language Filter")
    st.caption(
        "Block LLM outputs that contain hostile, offensive, or harmful language "
        "before they reach the user."
    )

    col_in, col_out = st.columns([1, 1])

    with col_in:
        prompt = st.text_area(
            "Prompt (instructs the LLM to produce toxic output)",
            value=DEFAULT_PROMPT,
            height=150,
            key="toxic_prompt",
        )
        run = st.button("▶ Run with Guard", key="toxic_run", type="primary")
        with st.expander("📋 Guard setup code"):
            st.code(GUARD_CODE, language="python")

    with col_out:
        if not api_key:
            st.warning("Enter your OpenAI API key in the sidebar.")
            return
        if run:
            with st.spinner("Running guard…"):
                result = run_guard(api_key, prompt, model)
            _render_result(result)


def _render_result(result: GuardResult) -> None:
    if result["install_hint"]:
        st.error("Validator not installed. Run:")
        st.code(result["install_hint"], language="bash")
        return

    if result["error"]:
        st.error(f"Error: {result['error']}")
        return

    if result["passed"]:
        st.success("✅ Guard passed — output is safe")
        st.markdown("**LLM response:**")
        st.write(result["output"])
    else:
        st.error("🚫 Guard blocked — toxic language detected in LLM output")
        if result["raw_output"]:
            with st.expander("What the LLM generated (blocked)"):
                st.write(result["raw_output"])
        st.info("The response was blocked before reaching the user.")
