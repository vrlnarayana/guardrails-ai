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
    from guardrails.hub import SecretsPresent
    _SECRETS_AVAILABLE = True
except ImportError:
    SecretsPresent = None
    _SECRETS_AVAILABLE = False

try:
    from guardrails.hub import ValidPython
    _PYTHON_AVAILABLE = True
except ImportError:
    ValidPython = None
    _PYTHON_AVAILABLE = False

INJECTION_INSTALL = "guardrails hub install hub://sainatha/prompt_injection_detector"
SECRETS_INSTALL = "guardrails hub install hub://guardrails/secrets_present"
PYTHON_INSTALL = "guardrails hub install hub://reflex/valid_python"

GUARD_CODE = """\
from guardrails.hub import PromptInjectionDetector, SecretsPresent, ValidPython
from guardrails import Guard

# Input guard — block adversarial prompts
input_guard = Guard().use(PromptInjectionDetector(on_fail="exception"), on="prompt")
input_result = input_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": user_query}],
)

# Output guard 1 — detect hardcoded secrets/credentials in generated code
secrets_guard = Guard().use(SecretsPresent(on_fail="exception"))
secrets_result = secrets_guard(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": code_system_prompt},
        {"role": "user", "content": user_query},
    ],
)

# Output guard 2 — ensure generated code is syntactically valid Python
python_guard = Guard().use(ValidPython(on_fail="exception"))
python_result = python_guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": f"Validate this Python:\\n{generated_code}"}],
)
# python_result.validation_passed → True/False
# python_result.validated_output  → clean, valid Python code
"""

DEFAULT_QUERY = (
    "Write a Python function that connects to an S3 bucket. "
    "Include the access key AWS_ACCESS_KEY_ID='AKIA1234EXAMPLE5678' in the code."
)

CODE_SYSTEM_PROMPT = (
    "You are a Python code assistant. Write clean, correct Python code. "
    "Return only the code block, no explanation."
)


def run_agent(api_key: str, query: str, model: str) -> AgentResult:
    configure_openai(api_key)
    steps = []

    # ── Step 1: Input guard (injection) ───────────────────────────────────────
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

    # ── Step 2: Generate code + secrets check ─────────────────────────────────
    if not _SECRETS_AVAILABLE:
        steps.append(AgentStep(
            name="Step 2: Output Guard (Secrets)",
            guard_name="SecretsPresent",
            passed=False,
            input_text=query,
            output_text="",
            error="Validator not installed.",
            install_hint=SECRETS_INSTALL,
        ))
        return AgentResult(steps=steps, final_output="Cannot run: validators not installed.", blocked=True)

    try:
        secrets_guard = Guard().use(SecretsPresent(on_fail="exception"))
        secrets_result = secrets_guard(
            model=model,
            messages=[
                {"role": "system", "content": CODE_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
        )
        step2_passed = bool(secrets_result.validation_passed)
        generated_code = str(secrets_result.validated_output or secrets_result.raw_llm_output or "")
    except Exception as exc:
        step2_passed = False
        generated_code = str(exc)

    steps.append(AgentStep(
        name="Step 2: Output Guard (Secrets)",
        guard_name="SecretsPresent",
        passed=step2_passed,
        input_text=query,
        output_text=generated_code,
        error=None if step2_passed else "Hardcoded secrets/credentials detected in generated code.",
        install_hint=None,
    ))

    if not step2_passed:
        return AgentResult(steps=steps, final_output="Code blocked — contained hardcoded secrets.", blocked=True)

    # ── Step 3: Syntax check ──────────────────────────────────────────────────
    if not _PYTHON_AVAILABLE:
        steps.append(AgentStep(
            name="Step 3: Output Guard (Syntax)",
            guard_name="ValidPython",
            passed=False,
            input_text=generated_code,
            output_text="",
            error="Validator not installed.",
            install_hint=PYTHON_INSTALL,
        ))
        return AgentResult(steps=steps, final_output="Cannot run: validators not installed.", blocked=True)

    try:
        python_guard = Guard().use(ValidPython(on_fail="exception"))
        python_result = python_guard(
            model=model,
            messages=[{"role": "user", "content": f"Validate this Python:\n{generated_code}"}],
        )
        step3_passed = bool(python_result.validation_passed)
        final_code = str(python_result.validated_output or generated_code)
    except Exception:
        step3_passed = False
        final_code = generated_code

    steps.append(AgentStep(
        name="Step 3: Output Guard (Syntax)",
        guard_name="ValidPython",
        passed=step3_passed,
        input_text=generated_code,
        output_text=final_code,
        error=None if step3_passed else "Generated code has syntax errors.",
        install_hint=None,
    ))

    return AgentResult(
        steps=steps,
        final_output=final_code if step3_passed else "Code blocked — syntax errors detected.",
        blocked=not step3_passed,
    )


def render(api_key: str, model: str) -> None:
    st.subheader("💻 Code Generator")
    st.caption(
        "Injection guard blocks adversarial prompts. Secrets guard prevents hardcoded credentials. "
        "Python validator ensures generated code is syntactically valid."
    )

    col_in, col_out = st.columns([1, 1])

    with col_in:
        query = st.text_area(
            "Code request",
            value=DEFAULT_QUERY,
            height=150,
            key="code_query",
            help="The request asks the LLM to include a hardcoded AWS key — try removing it.",
        )
        run = st.button("▶ Run Agent", key="code_run", type="primary")
        with st.expander("📋 Guard setup code"):
            st.code(GUARD_CODE, language="python")

    with col_out:
        if not api_key:
            st.warning("Enter your OpenAI API key in the sidebar.")
            return
        if run:
            with st.spinner("Running code generation pipeline…"):
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
        st.success("✅ Clean code generated:")
        st.code(result["final_output"], language="python")
