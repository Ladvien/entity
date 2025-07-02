from __future__ import annotations

"""Convenient built-in tool functions."""

from typing import Any, Mapping, cast

import httpx

from pipeline.plugins.tools.calculator_tool import SafeEvaluator


def calculator(expression: str) -> Any:
    """Evaluate an arithmetic expression."""
    evaluator = SafeEvaluator()
    return evaluator.evaluate(expression)


def search(query: str) -> str:
    """Return the first DuckDuckGo result snippet."""
    url = "https://api.duckduckgo.com/"
    params: Mapping[str, str | int | float | bool | None] = {
        "q": query,
        "format": "json",
        "no_redirect": 1,
        "no_html": 1,
    }
    try:
        resp = httpx.get(
            url,
            params=cast(Mapping[str, str | int | float | bool | None], params),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - network errors
        raise RuntimeError(f"Search request failed: {exc}") from exc

    topics = data.get("RelatedTopics")
    if topics and isinstance(topics, list):
        first = topics[0]
        if isinstance(first, dict) and first.get("Text"):
            return str(first["Text"])
    return "No results found."


def echo_llm(prompt: str) -> str:
    """Return the prompt unchanged."""
    return prompt
