import os


def configure_openai(api_key: str) -> None:
    """Set the OpenAI API key that Guardrails uses internally."""
    os.environ["OPENAI_API_KEY"] = api_key
