"""Updated tests for the news search tool."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_news_search import news_search

class TestNewsSearchTool:
    """Test cases for the news search tool."""
    
    @pytest.fixture(autouse=True)
    def setup_api_key(self):
        """Set up a dummy API key for testing."""
        original = os.environ.get("NEWSAPI_KEY")
        os.environ["NEWSAPI_KEY"] = "dummy_test_api_key"
        yield
        if original is None:
            del os.environ["NEWSAPI_KEY"]
        else:
            os.environ["NEWSAPI_KEY"] = original
    
    @pytest.mark.asyncio
    async def test_successful_news_search(self, mock_httpx_client):
        """Test successful news search with mock data."""
        client, response = mock_httpx_client
        
        # Mock response data
        mock_response = {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "source": {"id": "source1", "name": "News Source 1"},
                    "author": "Author 1",
                    "title": "Test News Article 1",
                    "description": "This is test news article 1",
                    "url": "https://example.com/news1",
                    "urlToImage": "https://example.com/image1.jpg",
                    "publishedAt": "2023-01-01T12:00:00Z",
                    "content": "Content of test news article 1"
                },
                {
                    "source": {"id": "source2", "name": "News Source 2"},
                    "author": "Author 2",
                    "title": "Test News Article 2",
                    "description": "This is test news article 2",
                    "url": "https://example.com/news2",
                    "urlToImage": "https://example.com/image2.jpg",
                    "publishedAt": "2023-01-02T12:00:00Z",
                    "content": "Content of test news article 2"
                }
            ]
        }
        
        # Configure response
        response.json = AsyncMock(return_value=mock_response)
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Call the function
            result = await news_search("test query")
            
            # Verify client was called correctly
            assert client.get.call_count == 1
            
            # Check the request parameters
            args, kwargs = client.get.call_args
            assert args[0] == "https://newsapi.org/v2/everything"
            assert kwargs["params"]["q"] == "test query"
            assert kwargs["headers"]["X-Api-Key"] == "dummy_test_api_key"
            
            # Verify result structure
            assert result["query"] == "test query"
            assert result["totalResults"] == 2
            assert len(result["articles"]) == 2
            assert result["articles"][0]["title"] == "Test News Article 1"
            assert result["articles"][1]["source"] == "News Source 2"
    
    @pytest.mark.asyncio
    async def test_empty_results(self, mock_httpx_client):
        """Test handling of empty search results."""
        client, response = mock_httpx_client
        
        # Mock empty response
        mock_response = {
            "status": "ok",
            "totalResults": 0,
            "articles": []
        }
        
        # Configure response
        response.json = AsyncMock(return_value=mock_response)
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Call the function
            result = await news_search("nonexistent_query")
            
            # Verify empty results handling
            assert result["query"] == "nonexistent_query"
            assert result["totalResults"] == 0
            assert len(result["articles"]) == 0
            assert "message" in result
            assert result["message"] == "No news articles found"
    
    @pytest.mark.asyncio
    async def test_api_error(self, mock_httpx_client):
        """Test handling of API errors."""
        client, response = mock_httpx_client
        
        # Mock error response
        response.status_code = 401
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Call the function
            result = await news_search("test query")
            
            # Verify error handling
            assert "error" in result
            assert "NewsAPI error: 401" in result["error"]
    
    @pytest.mark.asyncio
    async def test_date_calculation(self, mock_httpx_client):
        """Test that date is calculated correctly based on days parameter."""
        client, response = mock_httpx_client
        
        # Mock a successful response
        response.json = AsyncMock(return_value={"status": "ok", "articles": []})
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Calculate expected date
        today = datetime.now()
        days_ago_30 = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        days_ago_7 = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Test with default days (7)
            await news_search("test query")
            args, kwargs = client.get.call_args
            assert kwargs["params"]["from"] == days_ago_7
            
            # Reset mock
            client.get.reset_mock()
            
            # Test with custom days (30)
            await news_search("test query", days=30)
            args, kwargs = client.get.call_args
            assert kwargs["params"]["from"] == days_ago_30
    
    @pytest.mark.asyncio
    async def test_parameter_validation(self, mock_httpx_client):
        """Test validation of input parameters."""
        client, response = mock_httpx_client
        
        # Mock a successful response
        response.json = AsyncMock(return_value={"status": "ok", "articles": []})
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Test with days out of range (too low)
            await news_search("test query", days=0)
            args, kwargs = client.get.call_args
            assert kwargs["params"]["pageSize"] == 5  # Default max_results
            
            # Reset mock
            client.get.reset_mock()
            
            # Test with max_results out of range (too high)
            await news_search("test query", max_results=20)
            args, kwargs = client.get.call_args
            assert kwargs["params"]["pageSize"] == 10  # Capped at 10
