from tavily import TavilyClient
import os

def search_web(query: str):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return client.search(
        query,
        search_depth="advanced",
        max_results=5,
        include_answer=True,
        include_raw_content=False,  # ← Turn OFF raw content
        include_images=False
    )