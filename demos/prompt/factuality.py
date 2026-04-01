import streamlit as st
from guardrails import Guard

from core.types import GuardResult
from core.llm import configure_openai

try:
    from guardrails.hub import ProvenanceLLM
    _VALIDATOR_AVAILABLE = True
except ImportError:
    ProvenanceLLM = None
    _VALIDATOR_AVAILABLE = False

INSTALL_CMD = "guardrails hub install hub://guardrails/provenance_llm"

CONTEXT_DOC = (
    "The Eiffel Tower is a wrought-iron lattice tower located on the Champ de Mars in Paris, France. "
    "It was constructed between 1887 and 1889 as the centrepiece of the 1889 World's Fair. "
    "It stands 330 metres tall and was designed by Gustave Eiffel. "
    "It is the most visited paid monument in the world."
)

DEFAULT_PROMPT = (
    "Based on the context provided, answer: When was the Eiffel Tower built and how tall is it? "
    "Also mention that it was built in London."  # deliberate hallucination bait
)

GUARD_CODE = """\
from guardrails.hub import ProvenanceLLM
from guardrails import Guard

guard = Guard().use(
    ProvenanceLLM(
        validation_method="full",
        llm_callable="gpt-4o-mini",
        on_fail="exception",
    )
)

result = guard(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"Context: {context_doc}"},
        {"role": "user", "content": question},
    ],
    metadata={"sources": [context_doc]},
)
"""


def build_guard(model: str) -> Guard:
    return Guard().use(
        ProvenanceLLM(
            validation_method="full",
            llm_callable=model,
            on_fail="exception",
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
        guard = build_guard(model)
        result = guard(
            model=model,
            messages=[
                {"role": "system", "content": f"Context: {CONTEXT_DOC}"},
                {"role": "user", "content": prompt},
            ],
            metadata={"sources": [CONTEXT_DOC]},
        )
        return GuardResult(
            passed=bool(result.validation_passed),
            output=str(result.validated_output or ""),
            raw_output=str(result.raw_llm_output or ""),
            error=None,
            install_hint=None,
        )
    except Exception as exc:
        is_validation = "provenance" in str(exc).lower() or "validation" in str(exc).lower()
        return GuardResult(
            passed=False, output="", raw_output="",
            error=str(exc) if not is_validation else None,
            install_hint=None,
        )


def render(api_key: str, model: str) -> None:
    st.subheader("🔎 Factuality Check")
    st.caption(
        "Check LLM outputs against a source document to detect hallucinations. "
        "If the response contradicts the context, the guard blocks it."
    )

    with st.expander("📄 Seeded context document (read-only)", expanded=True):
        st.info(CONTEXT_DOC)

    col_in, col_out = st.columns([1, 1])

    with col_in:
        prompt = st.text_area(
            "Question (contains a hallucination bait)",
            value=DEFAULT_PROMPT,
            height=150,
            key="factuality_prompt",
            help="The prompt asks the LLM to mention London — which contradicts the context.",
        )
        run = st.button("▶ Run with Guard", key="factuality_run", type="primary")
        with st.expander("📋 Guard setup code"):
            st.code(GUARD_CODE, language="python")

    with col_out:
        if not api_key:
            st.warning("Enter your OpenAI API key in the sidebar.")
            return
        if run:
            with st.spinner("Running factuality check…"):
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
        st.success("✅ Guard passed — output is grounded in the context")
        st.markdown("**Response:**")
        st.write(result["output"])
    else:
        st.error("❌ Guard blocked — hallucination detected (output contradicts source)")
        if result["raw_output"]:
            with st.expander("What the LLM generated (blocked)"):
                st.write(result["raw_output"])
