"""Simple example tool used in tests."""


async def echo(text: str) -> str:
    """Return the provided text in upper case."""
    return text.upper()
