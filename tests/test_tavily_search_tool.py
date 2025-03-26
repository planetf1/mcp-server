"""Tests for the Tavily search tool."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_tavily_search import tavily_search

class TestTavilySearchTool:
    """Test cases for the Tavily search tool."""
    
    @pytest.fixture(autouse=True)
    def setup_api_key(self):
        """Set up a dummy API key for testing."""
        original = os.environ.get("TAVILY_API_KEY")
        os.environ["TAVILY_API_KEY"] = "dummy_test_api_key"
        yield
        if original is None:
            del os.environ["TAVILY_API_KEY"]
        else:
            os.environ["TAVILY_API_KEY"] = original
    
    @pytest.mark.asyncio
    async def test_successful_search(self, mock_httpx_client):
        """Test successful search with mock data."""
        client, response = mock_httpx_client
        
        # Mock successful search response
        mock_results = {
            "results": [
                {
                    "title": "Test Result 1",
                    "url": "https://example.com/1",
                    "content": "This is the first test result with detailed content.",
                    "score": 0.95
                },
                {
                    "title": "Test Result 2",
                    "url": "https://example.com/2",
                    "content": "This is the second test result with some information.",
                    "score": 0.85
                }
            ],
            "query": "test query",
            "search_depth": "basic"
        }
        response.json = AsyncMock(return_value=mock_results)
        response.status_code = 200
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Call the actual function, not a mock
            result = await tavily_search("test query")
            
            # Verify client was called correctly
            assert client.post.call_count == 1
            
            # Check the payload from the API call
            args, kwargs = client.post.call_args
            assert kwargs["json"]["query"] == "test query"
            assert kwargs["json"]["api_key"] == "dummy_test_api_key"
            assert kwargs["json"]["search_depth"] == "basic"
            
            # Verify result structure
            assert len(result["results"]) == 2
            assert result["results"][0]["title"] == "Test Result 1"
            assert result["results"][1]["url"] == "https://example.com/2"
    
    @pytest.mark.asyncio
    async def test_advanced_search_depth(self, mock_httpx_client):
        """Test search with advanced depth parameter."""
        client, response = mock_httpx_client
        
        # Create mock response
        mock_results = {
            "results": [{"title": "Advanced Result", "url": "https://example.com/advanced"}],
            "query": "test query",
            "search_depth": "advanced"
        }
        response.json = AsyncMock(return_value=mock_results)
        response.status_code = 200
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Call the actual function, not a mock
            result = await tavily_search("test query", search_depth="advanced")
            
            # Verify depth parameter was used correctly
            args, kwargs = client.post.call_args
            assert kwargs["json"]["search_depth"] == "advanced"
            
            # Verify result structure
            assert result["search_depth"] == "advanced"
    
    @pytest.mark.asyncio
    async def test_empty_results(self, mock_httpx_client):
        """Test handling of empty search results."""
        client, response = mock_httpx_client
        
        # Mock empty results
        mock_results = {
            "results": [],
            "query": "nonexistent query"
        }
        response.json = AsyncMock(return_value=mock_results)
        response.status_code = 200
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Call the actual function
            result = await tavily_search("nonexistent query")
            
            # Verify empty results are handled properly
            assert len(result["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_httpx_client):
        """Test error handling for API errors."""
        client, response = mock_httpx_client
        
        # Mock error response
        response.status_code = 401
        response.text = "Unauthorized: Invalid API key"
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            with pytest.raises(Exception) as excinfo:
                await tavily_search("test query")
            
            # Verify error message contains API error details
            error_message = str(excinfo.value)
            assert "Tavily API error" in error_message
            assert "401" in error_message
