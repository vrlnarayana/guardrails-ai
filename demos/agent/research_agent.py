import streamlit as st
from guardrails import Guard

from core.types import AgentResult, AgentStep
from core.llm import configure_openai

try:
    from guardrails.hub import PromptInjectionDetector
    _INJECTION_AVAILABLE = True
except ImportError:
    PromptInjectionDetector = None
    _INJECTION_AVAILABLE = False

try:
    from guardrails.hub import ProvenanceLLM
    _PROVENANCE_AVAILABLE = True
except ImportError:
    ProvenanceLLM = None
    _PROVENANCE_AVAILABLE = False

INJECTION_INSTALL = "guardrails hub install hub://sainatha/prompt_injection_detector"
PROVENANCE_INSTALL = "guardrails hub install hub://guardrails/provenance_llm"

GUARD_CODE = """\
from guardrails.hub import PromptInjectionDetector, ProvenanceLLM
from guardrails import Guard

# Input guard — block adversarial queries
input_guard = Guard().use(PromptInjectionDetector(on_fail="exception"), on="prompt")
input_result = input_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": user_query}],
)

# Output guard — ensure summary is grounded in source document
output_guard = Guard().use(ProvenanceLLM(
    validation_method="full",
    llm_callable="gpt-4o-mini",
    on_fail="exception",
))
output_result = output_guard(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"Summarise based only on this source:\\n{source_doc}"},
        {"role": "user", "content": user_query},
    ],
    metadata={"sources": [source_doc]},
)
# output_result.validation_passed → True/False
# output_result.validated_output  → grounded summary
"""

SOURCE_DOC = (
    "Photosynthesis is the process by which green plants, algae, and some bacteria convert "
    "light energy (usually from the sun) into chemical energy stored as glucose. "
    "The process takes place mainly in the chloroplasts of plant cells. "
    "The overall equation is: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂. "
    "Photosynthesis has two stages: the light-dependent reactions and the Calvin cycle."
)

DEFAULT_QUERY = "Summarise how photosynthesis works and mention that it requires darkness to function."


def run_agent(api_key: str, query: str, model: str) -> AgentResult:
    configure_openai(api_key)
    steps = []

    # ── Step 1: Input guard ───────────────────────────────────────────────────
    if not _INJECTION_AVAILABLE:
        steps.append(AgentStep(
            name="Step 1: Input Guard",
            guard_name="PromptInjectionDetector",
            passed=False,
            input_text=query,
            output_text="",
            error="Validator not installed.",
            install_hint=INJECTION_INSTALL,
        ))
        return AgentResult(steps=steps, final_output="Cannot run: validators not installed.", blocked=True)

    try:
        input_guard = Guard().use(PromptInjectionDetector(on_fail="exception"), on="prompt")
        input_result = input_guard(
            model=model,
            messages=[{"role": "user", "content": query}],
        )
        step1_passed = bool(input_result.validation_passed)
    except Exception:
        step1_passed = False

    steps.append(AgentStep(
        name="Step 1: Input Guard",
        guard_name="PromptInjectionDetector",
        passed=step1_passed,
        input_text=query,
        output_text=query if step1_passed else "",
        error=None if step1_passed else "Prompt injection detected.",
        install_hint=None,
    ))

    if not step1_passed:
        return AgentResult(steps=steps, final_output="Request blocked by input guard.", blocked=True)

    # ── Step 2: Summarise with provenance check ────────────────────────────────
    if not _PROVENANCE_AVAILABLE:
        steps.append(AgentStep(
            name="Step 2: Output Guard",
            guard_name="ProvenanceLLM",
            passed=False,
            input_text=query,
            output_text="",
            error="Validator not installed.",
            install_hint=PROVENANCE_INSTALL,
        ))
        return AgentResult(steps=steps, final_output="Cannot run: validators not installed.", blocked=True)

    try:
        output_guard = Guard().use(ProvenanceLLM(
            validation_method="full",
            llm_callable=model,
            on_fail="exception",
        ))
        output_result = output_guard(
            model=model,
            messages=[
                {"role": "system", "content": f"Summarise based only on this source:\n{SOURCE_DOC}"},
                {"role": "user", "content": query},
            ],
            metadata={"sources": [SOURCE_DOC]},
        )
        step2_passed = bool(output_result.validation_passed)
        summary = str(output_result.validated_output or output_result.raw_llm_output or "")
    except Exception as exc:
        step2_passed = False
        summary = str(exc)

    steps.append(AgentStep(
        name="Step 2: Output Guard",
        guard_name="ProvenanceLLM",
        passed=step2_passed,
        input_text=query,
        output_text=summary,
        error=None if step2_passed else "Summary contains claims not supported by source.",
        install_hint=None,
    ))

    return AgentResult(
        steps=steps,
        final_output=summary if step2_passed else "Summary blocked — contained unsupported claims.",
        blocked=not step2_passed,
    )


def render(api_key: str, model: str) -> None:
    st.subheader("📰 Research Summariser")
    st.caption(
        "Injection guard blocks adversarial queries. Provenance guard ensures the summary "
        "stays grounded in the source document."
    )

    with st.expander("📄 Source document", expanded=False):
        st.info(SOURCE_DOC)

    col_in, col_out = st.columns([1, 1])

    with col_in:
        query = st.text_area(
            "Summarisation request",
            value=DEFAULT_QUERY,
            height=120,
            key="research_query",
            help="The query contains a hallucination bait ('requires darkness'). Try removing it.",
        )
        run = st.button("▶ Run Agent", key="research_run", type="primary")
        with st.expander("📋 Guard setup code"):
            st.code(GUARD_CODE, language="python")

    with col_out:
        if not api_key:
            st.warning("Enter your OpenAI API key in the sidebar.")
            return
        if run:
            with st.spinner("Running research pipeline…"):
                result = run_agent(api_key, query, model)
            _render_result(result)


def _render_result(result: AgentResult) -> None:
    st.markdown("**Pipeline trace:**")
    for step in result["steps"]:
        if step["install_hint"]:
            st.error(f"**{step['name']}** — {step['guard_name']}: not installed")
            st.code(step["install_hint"], language="bash")
        elif step["passed"]:
            st.success(f"✅ **{step['name']}** — {step['guard_name']}: passed")
        else:
            st.error(f"❌ **{step['name']}** — {step['guard_name']}: {step['error']}")

    st.divider()
    if result["blocked"]:
        st.error("🚫 Pipeline blocked")
    else:
        st.success("✅ Grounded summary:")
        st.write(result["final_output"])
