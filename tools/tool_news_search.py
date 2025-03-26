"""
News search tool using NewsAPI.
"""
import os
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from mcp_instance import mcp

@mcp.tool()
async def news_search(query: str, days: int = 7, max_results: int = 5,
                   sources: Optional[str] = None, domains: Optional[str] = None,
                   language: str = "en", sort_by: str = "relevancy") -> Dict[str, Any]:
    """
    Search for news articles using NewsAPI
    
    Args:
        query: The search query string
        days: Number of days to look back (1-30)
        max_results: Maximum number of results to return (1-10)
        sources: Comma-separated list of news sources
        domains: Comma-separated list of domains
        language: Two-letter language code
        sort_by: Sort method (relevancy, popularity, publishedAt)
        
    Returns:
        News articles matching the query
    """
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        return {"error": "NEWSAPI_KEY environment variable is not set"}
        
    # Validate parameters
    if not (1 <= days <= 30):
        days = min(max(days, 1), 30)
    
    if not (1 <= max_results <= 10):
        max_results = min(max(max_results, 1), 10)
        
    # Calculate date range
    from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    try:
        # Use direct API call with httpx instead of a mock client
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "from": from_date,
                    "language": language,
                    "sortBy": sort_by,
                    "pageSize": max_results,
                    "sources": sources,
                    "domains": domains
                },
                headers={
                    "X-Api-Key": api_key
                }
            )
            
            if response.status_code != 200:
                return {"error": f"NewsAPI error: {response.status_code}"}
            
            data = await response.json()
            
            # Format the response
            articles = data.get("articles", [])
            
            if not articles:
                return {
                    "query": query,
                    "totalResults": 0,
                    "articles": [],
                    "message": "No news articles found"
                }
                
            return {
                "query": query,
                "totalResults": data.get("totalResults", len(articles)),
                "articles": [
                    {
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                        "url": article.get("url"),
                        "publishedAt": article.get("publishedAt"),
                        "description": article.get("description")
                    }
                    for article in articles[:max_results]
                ]
            }
    except Exception as e:
        return {"error": f"Error fetching news: {str(e)}"}
