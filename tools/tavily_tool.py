from tavily import TavilyClient
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def tavily_search(query: str, max_results: int = 5) -> dict:
    """Return evidence, never presentation-ready prose.

    Callers must keep source URLs and timestamps attached to any travel fact.
    """
    fetched_at = datetime.now(timezone.utc).isoformat()
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"success": False, "data": [], "source": "Tavily", "fetched_at": fetched_at,
                "error": "TAVILY_API_KEY is not configured"}
    try:
        response = TavilyClient(api_key=api_key).search(query=query, max_results=max_results)
        data = [
            {
                "title": item.get("title", "Untitled"),
                "url": item.get("url"),
                "snippet": item.get("content", "").strip(),
                "published_date": item.get("published_date"),
            }
            for item in response.get("results", [])
        ]
        return {"success": True, "data": data, "source": "Tavily", "fetched_at": fetched_at,
                "error": None}
    except Exception as exc:
        return {"success": False, "data": [], "source": "Tavily", "fetched_at": fetched_at,
                "error": str(exc)}
