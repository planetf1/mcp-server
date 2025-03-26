import os
import httpx
from datetime import datetime, timedelta
from mcp_instance import mcp

@mcp.tool()
async def news_search(query: str, days: int = 7, max_results: int = 5) -> dict:
    """
    Search for news articles using NewsAPI
    
    Args:
        query: The search query string
        days: Number of days to look back (1-30)
        max_results: Maximum number of results to return (1-10)
        
    Returns:
        News articles matching the query
    """
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        raise ValueError("NEWSAPI_KEY environment variable is not set")
        
    if not (1 <= days <= 30):
        days = min(max(days, 1), 30)
    
    if not (1 <= max_results <= 10):
        max_results = min(max(max_results, 1), 10)
        
    # Calculate date range
    from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": from_date,
                "sortBy": "relevancy",
                "pageSize": max_results,
                "language": "en"
            },
            headers={
                "X-Api-Key": api_key
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"NewsAPI error: {response.status_code} - {response.text}")
            
        data = response.json()
        
        # Format the response
        articles = data.get("articles", [])
        return {
            "query": query,
            "totalResults": data.get("totalResults", 0),
            "articles": [
                {
                    "title": article.get("title"),
                    "source": article.get("source", {}).get("name"),
                    "author": article.get("author"),
                    "url": article.get("url"),
                    "publishedAt": article.get("publishedAt"),
                    "description": article.get("description")
                }
                for article in articles
            ]
        }
