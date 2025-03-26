"""
DuckDuckGo search tool for retrieving search results.
"""
import httpx
from bs4 import BeautifulSoup
from mcp_instance import mcp

@mcp.tool()
async def duckduckgo_search(query: str, max_results: int = 5) -> list:
    """
    Perform a search using DuckDuckGo
    
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
            "https://html.duckduckgo.com/html/",
            params={"q": query}
        )
        
        if response.status_code != 200:
            raise Exception(f"DuckDuckGo search error: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all search result containers
        results = []
        for result_element in soup.find_all("div", class_="result"):
            # Extract title and URL
            title_element = result_element.find("h2", class_="result__title").find("a")
            title = title_element.text.strip()
            url = title_element.get("href")
            
            # Extract snippet
            snippet_elements = result_element.find_all("div", class_="result__snippet")
            snippet = snippet_elements[0].text.strip() if snippet_elements else ""
            
            # Add to results list
            results.append({
                "title": title,
                "url": url,
                "snippet": snippet
            })
            
            # Stop once we have enough results
            if len(results) >= max_results:
                break
        
        return results
