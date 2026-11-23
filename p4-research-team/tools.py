import os
import re
from pathlib import Path
from langchain_core.tools import tool
from tavily import TavilyClient


@tool
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

@tool
def save_brief(company: str, content: str) -> str:
    """Save the finished company brief as a Markdown file in the briefs folder.

    Call this exactly once, after the brief is completely written.

    Args:
        company: The company name, exactly as given in the request.
        content: The full brief in Markdown.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-") or "company"
    out_dir = Path("briefs")
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"{slug}.md"
    path.write_text(content, encoding="utf-8")
    return f"Saved to {path.as_posix()}"