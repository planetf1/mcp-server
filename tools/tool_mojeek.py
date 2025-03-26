import httpx
from bs4 import BeautifulSoup
from mcp_instance import mcp

@mcp.tool()
async def mojeek_search(query: str, max_results: int = 5) -> list:
    """
    Perform a search using the Mojeek search engine
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (1-10)
        
    Returns:
        List of search results with title, url, and snippet
    """
    if not (1 <= max_results <= 10):
        max_results = min(max(max_results, 1), 10)
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.mojeek.com/search",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Mojeek search error: {response.status_code}")
            
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        for result in soup.select(".results-standard .result")[:max_results]:
            title_elem = result.select_one(".title")
            url_elem = result.select_one(".url")
            snippet_elem = result.select_one(".s")
            
            if title_elem and url_elem and snippet_elem:
                results.append({
                    "title": title_elem.text.strip(),
                    "url": url_elem.text.strip(),
                    "snippet": snippet_elem.text.strip()
                })
                
        return results
