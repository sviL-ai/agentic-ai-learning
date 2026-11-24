import os
from langchain_core.tools import tool

EXA_TEXT_CHARS = 3000  # per-result cap on page text, keeps tool output (and history) small


def build_search_tool(provider: str = "exa", include_domains: list[str] | None = None):
    if provider == "tavily":
        from langchain_tavily import TavilySearch

        kwargs = {"include_domains": include_domains} if include_domains else {}
        return TavilySearch(max_results=5, search_depth="advanced", **kwargs)

    from exa_py import Exa

    exa = Exa(api_key=os.environ["EXA_API_KEY"])

    @tool
    def web_search(query: str, num_results: int = 5) -> str:
        """Search the web for Indian legal sources (statutes, judgments, legal analysis).

        Returns each result's title, URL, date, key highlights and an excerpt of the page.
        Write the query as a specific, descriptive search, e.g.
        'Supreme Court anticipatory bail guidelines Section 438 CrPC Section 482 BNSS'.
        """
        try:
            kwargs = {"include_domains": include_domains} if include_domains else {}
            res = exa.search_and_contents(
                query,
                num_results=min(num_results, 8),
                type="auto",
                text={"max_characters": EXA_TEXT_CHARS},
                highlights={"num_sentences": 3, "highlights_per_url": 3},
                **kwargs,
            )
        except Exception as e:  # rate limits, bad key, network
            return f"Search failed: {e}"

        if not res.results:
            return "No results found."

        blocks = []
        for i, r in enumerate(res.results, 1):
            highlights = "\n".join(f"- {h}" for h in (r.highlights or []))
            blocks.append(
                f"[{i}] {r.title}\n"
                f"URL: {r.url}\n"
                f"Published: {r.published_date or 'unknown'}\n"
                f"Highlights:\n{highlights or '(none)'}\n"
                f"Excerpt: {(r.text or '').strip()}"
            )
        return "\n\n".join(blocks)

    return web_search