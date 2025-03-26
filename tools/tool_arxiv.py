import httpx
import xml.etree.ElementTree as ET
from mcp_instance import mcp

@mcp.tool()
async def arxiv_search(query: str, max_results: int = 5, sort_by: str = "relevance") -> list:
    """
    Search arXiv for research papers
    
    Args:
        query: The search query
        max_results: Maximum number of results to return (1-10)
        sort_by: Sort order - 'relevance', 'lastUpdatedDate', or 'submittedDate'
        
    Returns:
        List of research papers with title, authors, abstract, etc.
    """
    if not (1 <= max_results <= 10):
        max_results = min(max(max_results, 1), 10)
        
    sort_options = {
        "relevance": "relevance", 
        "lastUpdatedDate": "lastUpdatedDate", 
        "submittedDate": "submittedDate"
    }
    sort = sort_options.get(sort_by, "relevance")
    
    # URL encode the query
    query = query.replace(' ', '+')
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}&sortBy={sort}"
        )
        
        if response.status_code != 200:
            raise Exception(f"arXiv API error: {response.status_code}")
            
        # Parse XML response
        root = ET.fromstring(response.text)
        
        # Define namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom'}
        
        entries = root.findall('atom:entry', ns)
        results = []
        
        for entry in entries:
            title = entry.find('atom:title', ns).text.strip()
            summary = entry.find('atom:summary', ns).text.strip()
            published = entry.find('atom:published', ns).text
            
            # Get authors
            authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
            
            # Get URL
            links = entry.findall('atom:link', ns)
            url = next((link.get('href') for link in links if link.get('type') == 'text/html'), "")
            
            # Get categories
            categories = [cat.get('term') for cat in entry.findall('atom:category', ns)]
            
            # Get PDF link
            pdf_url = next((link.get('href') for link in links if link.get('title') == 'pdf'), "")
            
            results.append({
                "title": title,
                "authors": authors,
                "summary": summary,
                "published": published,
                "url": url,
                "pdf_url": pdf_url,
                "categories": categories
            })
            
        return results
