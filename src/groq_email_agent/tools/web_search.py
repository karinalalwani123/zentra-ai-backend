from tavily import TavilyClient
import os

def search_web(query: str):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return client.search(query)