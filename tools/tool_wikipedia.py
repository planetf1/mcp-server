import httpx
from mcp_instance import mcp

@mcp.tool()
async def wikipedia_search(query: str, limit: int = 3) -> dict:
    """
    Search Wikipedia and retrieve content
    
    Args:
        query: The search query
        limit: Maximum number of results to return (1-5)
        
    Returns:
        Wikipedia search results and article extracts
    """
    if not (1 <= limit <= 5):
        limit = min(max(limit, 1), 5)
        
    async with httpx.AsyncClient() as client:
        # First search for articles
        search_response = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": limit
            }
        )
        
        if search_response.status_code != 200:
            raise Exception(f"Wikipedia API error: {search_response.status_code}")
            
        # Need to await the json() method since it's asynchronous
        search_data = await search_response.json()
        results = search_data.get("query", {}).get("search", [])
        
        if not results:
            return {"results": [], "message": "No articles found"}
            
        # Get article extracts for each result
        page_ids = [str(result["pageid"]) for result in results]
        extract_response = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "pageids": "|".join(page_ids),
                "prop": "extracts|info",
                "inprop": "url",
                "exintro": True,
                "explaintext": True
            }
        )
        
        if extract_response.status_code != 200:
            raise Exception(f"Wikipedia API error: {extract_response.status_code}")
            
        # Need to await the json() method here too
        extract_data = await extract_response.json()
        pages = extract_data.get("query", {}).get("pages", {})
        
        detailed_results = []
        for page_id in page_ids:
            if page_id in pages:
                page = pages[page_id]
                detailed_results.append({
                    "title": page.get("title", ""),
                    "url": page.get("fullurl", ""),
                    "extract": page.get("extract", ""),
                    "pageid": page_id
                })
                
        return {"results": detailed_results}
