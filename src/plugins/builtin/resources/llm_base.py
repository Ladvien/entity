from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Simple container for LLM output."""

    content: str


class LLM:
    """Placeholder LLM type used in tests."""

    pass
