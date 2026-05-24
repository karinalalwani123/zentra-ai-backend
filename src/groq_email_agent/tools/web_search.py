from tavily import TavilyClient
import os

def search_web(query: str):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return client.search(
        query,
        search_depth="advanced",  # Uses more quota but better results
        max_results=10,           # Get more results
        include_answer=True,      # Get direct answer
        include_raw_content=True, # Get full content
        include_images=False
    )