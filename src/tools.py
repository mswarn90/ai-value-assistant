import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

SEARCH_TOOL = {
    "name": "search_web",
    "description": "Search the web for current information about a company, industry trends, or topic. Use this to gather facts before writing the research brief.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string"
            }
        },
        "required": ["query"]
    }
}


def run_search(query: str) -> str:
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query=query, max_results=5, search_depth="advanced")
    results = []
    for r in response.get("results", []):
        results.append(f"**{r['title']}**\n{r['url']}\n{r['content']}")
    return "\n\n---\n\n".join(results) if results else "No results found."
