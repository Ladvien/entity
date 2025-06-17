from langchain_core.tools import tool
import httpx
import json


@tool
def web_search(query: str) -> str:
    """Search the web for information"""
    # Simple web search using DuckDuckGo API
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        response = httpx.get(url, timeout=10)
        data = response.json()

        if data.get("AbstractText"):
            return data["AbstractText"]
        elif data.get("RelatedTopics"):
            results = []
            for topic in data["RelatedTopics"][:3]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append(topic["Text"])
            return "\n".join(results) if results else "No results found"
        else:
            return "No results found"
    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def calculator(expression: str) -> str:
    """Calculate mathematical expressions"""
    try:
        # Simple eval for basic math (be careful in production!)
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"


@tool
def file_reader(filepath: str) -> str:
    """Read text files"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:1000]  # Limit to first 1000 chars
    except Exception as e:
        return f"File read error: {str(e)}"


def get_tools():
    """Return list of available tools"""
    return [web_search, calculator, file_reader]
