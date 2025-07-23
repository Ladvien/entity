"""Simple example tool used in tests."""


async def echo(text: str, results: list[str] | None = None) -> str:
    """Return the provided text in upper case."""
    if results is not None:
        results.append(text)
    return text.upper()
