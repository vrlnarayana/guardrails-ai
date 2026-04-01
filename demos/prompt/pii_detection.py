import streamlit as st
from guardrails import Guard

from core.types import GuardResult
from core.llm import configure_openai

try:
    from guardrails.hub import DetectPII
    _VALIDATOR_AVAILABLE = True
except ImportError:
    DetectPII = None
    _VALIDATOR_AVAILABLE = False

INSTALL_CMD = "guardrails hub install hub://guardrails/detect_pii"

DEFAULT_PROMPT = (
    "My name is Sarah Johnson and my email is sarah.johnson@example.com. "
    "Please summarise GDPR in 3 bullet points."
)

GUARD_CODE = """\
from guardrails.hub import DetectPII
from guardrails import Guard

guard = Guard().use(
    DetectPII(
        pii_entities=["EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER"],
        on_fail="fix",
    )
)

result = guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)
# result.validation_passed → True/False
# result.validated_output  → sanitised text
# result.raw_llm_output    → original LLM response
"""


def build_guard() -> Guard:
    return Guard().use(
        DetectPII(
            pii_entities=["EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER"],
            on_fail="fix",
        )
    )


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
    st.subheader("🔍 PII Detection")
    st.caption(
        "Detect and redact personally identifiable information (names, emails, phone numbers) "
        "before the LLM response is shown to users."
    )

    col_in, col_out = st.columns([1, 1])

    with col_in:
        prompt = st.text_area(
            "Input prompt",
            value=DEFAULT_PROMPT,
            height=150,
            key="pii_prompt",
            help="The pre-loaded prompt contains PII — try removing it to see the guard pass.",
        )
        run = st.button("▶ Run with Guard", key="pii_run", type="primary")
        with st.expander("📋 Guard setup code"):
            st.code(GUARD_CODE, language="python")

    with col_out:
        if not api_key:
            st.warning("Enter your OpenAI API key in the sidebar to run this demo.")
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
        st.success("✅ Guard passed — no PII detected in output")
    else:
        st.error("❌ Guard triggered — PII detected and redacted")

    if result["raw_output"]:
        with st.expander("Without Guard (raw LLM output)"):
            st.write(result["raw_output"])

    st.markdown("**With Guard (sanitised):**")
    st.write(result["output"] or "_Output was blocked._")
