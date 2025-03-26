import os
import httpx
from mcp_instance import mcp

@mcp.tool()
async def tavily_search(query: str, search_depth: str = "basic") -> dict:
    """
    Perform a search using the Tavily API
    
    Args:
        query: The search query string
        search_depth: The depth of search - 'basic' or 'comprehensive'
        
    Returns:
        Search results from Tavily
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set")
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={
                "query": query,
                "search_depth": search_depth,
                "include_domains": [],
                "exclude_domains": [],
                "max_results": 5
            },
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": api_key
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Tavily API error: {response.status_code} - {response.text}")
            
        return response.json()
