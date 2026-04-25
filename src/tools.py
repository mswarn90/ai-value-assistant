import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

SEARCH_TOOL = {
    "name": "search_web",
    "description": "Search the web for current information about a company, industry trends, or topic. Use days=90 when you need recent news from the last 90 days specifically.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string"
            },
            "days": {
                "type": "integer",
                "description": "Limit results to the last N days. Use 90 for recent news searches. Omit for broader searches."
            }
        },
        "required": ["query"]
    }
}


def run_search(query: str, days: int = None) -> str:
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    kwargs = {"query": query, "max_results": 5, "search_depth": "advanced"}
    if days:
        kwargs["days"] = days
    response = client.search(**kwargs)
    results = []
    for r in response.get("results", []):
        results.append(f"**{r['title']}**\n{r['url']}\n{r['content']}")
    return "\n\n---\n\n".join(results) if results else "No results found."
