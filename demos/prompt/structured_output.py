import json
from typing import List

import streamlit as st
from guardrails import Guard
from pydantic import BaseModel, Field

from core.types import GuardResult
from core.llm import configure_openai

# No hub validator needed — Guard.for_pydantic() is built-in
_VALIDATOR_AVAILABLE = True
INSTALL_CMD = ""

DEFAULT_PROMPT = (
    "Write a product review for a noise-cancelling headphone you recently purchased."
)

GUARD_CODE = """\
from pydantic import BaseModel, Field
from guardrails import Guard

class ProductReview(BaseModel):
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5")
    summary: str = Field(description="One-sentence summary")
    pros: list[str] = Field(description="List of pros")

guard = Guard.for_pydantic(output_class=ProductReview)

result = guard(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)
# result.validated_output is a ProductReview instance (or dict)
"""


class ProductReview(BaseModel):
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5")
    summary: str = Field(description="One-sentence summary of the product")
    pros: List[str] = Field(description="List of positive aspects")


def build_guard() -> Guard:
    return Guard.for_pydantic(output_class=ProductReview)


def run_guard(api_key: str, prompt: str, model: str) -> GuardResult:
    configure_openai(api_key)
    try:
        guard = build_guard()
        result = guard(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        output = result.validated_output
        output_str = json.dumps(output, indent=2) if isinstance(output, dict) else str(output or "")
        return GuardResult(
            passed=bool(result.validation_passed),
            output=output_str,
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
    st.subheader("📐 Structured Output")
    st.caption(
        "Force the LLM to return a valid, schema-conforming JSON object. "
        "If it doesn't, Guardrails retries or raises."
    )

    col_in, col_out = st.columns([1, 1])

    with col_in:
        prompt = st.text_area(
            "Prompt",
            value=DEFAULT_PROMPT,
            height=150,
            key="structured_prompt",
        )
        st.markdown("**Required schema:**")
        st.code(
            "{\n  rating: int (1–5),\n  summary: str,\n  pros: list[str]\n}",
            language="json",
        )
        run = st.button("▶ Run with Guard", key="structured_run", type="primary")
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
    if result["error"]:
        st.error(f"Error: {result['error']}")
        return

    if result["passed"]:
        st.success("✅ Guard passed — valid structured output returned")
        st.markdown("**Parsed output (JSON):**")
        try:
            st.json(json.loads(result["output"]))
        except Exception:
            st.code(result["output"])
    else:
        st.error("❌ Guard failed — LLM did not return valid schema")
        if result["raw_output"]:
            with st.expander("Raw LLM output (failed schema check)"):
                st.write(result["raw_output"])
