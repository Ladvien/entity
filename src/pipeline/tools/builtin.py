from __future__ import annotations

"""Convenient built-in tool functions."""

from typing import Any

import httpx

from ..exceptions import ResourceError


def calculator(expression: str) -> Any:
    """Evaluate an arithmetic expression."""
    from plugins.contrib.tools.calculator_tool import SafeEvaluator

    evaluator = SafeEvaluator()
    return evaluator.evaluate(expression)


def search(query: str) -> str:
    """Return the first DuckDuckGo result snippet."""
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - network errors
        raise ResourceError(f"Search request failed: {exc}") from exc

    topics = data.get("RelatedTopics")
    if topics and isinstance(topics, list):
        first = topics[0]
        if isinstance(first, dict) and first.get("Text"):
            return str(first["Text"])
    return "No results found."


def echo_llm(prompt: str) -> str:
    """Return the prompt unchanged."""
    return prompt
