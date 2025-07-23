import httpx


async def web_search(query: str, results: list[str] | None = None) -> str:
    """Return a summary from DuckDuckGo Instant Answer."""
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10)
        data = resp.json()

    summary = data.get("AbstractText") or data.get("Heading") or ""
    if results is not None:
        results.append(summary)
    return summary
