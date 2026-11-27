import os
from crewai.tools import tool
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

api_key = os.environ.get("TAVILY_API_KEY")

@tool("web_search")
def web_search(query: str) -> dict:
    """Search the web for current or factual information such as company
    details, products, news and recent events. Returns a short list of
    results, each with a title, url and content snippet.

    Call it several times with different, specific queries instead of one
    broad query.

    Args:
        query: A concise search query, e.g. "Acme Corp products and services".
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return {"error": "TAVILY_API_KEY is not set."}

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=5, search_depth="basic")
    except Exception as e:
        return {"error": f"Web search failed: {e}"}

    return {
        "query": query,
        "results": [
            {"title": r["title"], "url": r["url"], "content": r["content"]}
            for r in response.get("results", [])
        ],
    }