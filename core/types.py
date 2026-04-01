from typing import List, Optional
from typing_extensions import TypedDict


class GuardResult(TypedDict):
    passed: bool
    output: str          # validated/sanitised output shown to user
    raw_output: str      # raw LLM output before validation
    error: Optional[str] # human-readable error if guard raised
    install_hint: Optional[str]  # hub install command if validator missing


class AgentStep(TypedDict):
    name: str            # e.g. "Step 1: Input Guard"
    guard_name: str      # e.g. "PromptInjectionDetector"
    passed: bool
    input_text: str      # what was fed to this step's guard
    output_text: str     # what came out
    error: Optional[str]
    install_hint: Optional[str]


class AgentResult(TypedDict):
    steps: List[AgentStep]
    final_output: str
    blocked: bool
