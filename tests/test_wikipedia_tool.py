"""Tests for the Wikipedia search tool."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_wikipedia import wikipedia_search

class TestWikipediaTool:
    """Test cases for the Wikipedia search tool."""
    
    @pytest.mark.asyncio
    async def test_valid_search(self):
        """Test successful Wikipedia search with valid results."""
        # Create mock response objects
        search_response = AsyncMock()
        search_response.status_code = 200
        
        # Important: Set json() to return an awaitable that resolves to our test data
        search_data = {
            "query": {
                "search": [
                    {
                        "title": "Python (programming language)",
                        "pageid": 123
                    },
                    {
                        "title": "Python (genus)",
                        "pageid": 456
                    }
                ]
            }
        }
        search_response.json = AsyncMock(return_value=search_data)
        
        extract_response = AsyncMock()
        extract_response.status_code = 200
        
        # Important: Set json() to return an awaitable that resolves to our test data
        extract_data = {
            "query": {
                "pages": {
                    "123": {
                        "title": "Python (programming language)",
                        "fullurl": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                        "extract": "Python is a high-level programming language."
                    },
                    "456": {
                        "title": "Python (genus)",
                        "fullurl": "https://en.wikipedia.org/wiki/Python_(genus)",
                        "extract": "Python is a genus of snakes."
                    }
                }
            }
        }
        extract_response.json = AsyncMock(return_value=extract_data)
        
        # Create mock client
        mock_client = AsyncMock()
        mock_client.get.side_effect = [search_response, extract_response]
        
        # Mock the context manager properly
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = mock_client
        
        # Patch AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            result = await wikipedia_search("python", limit=2)
        
            # Verify the correct requests were made
            assert mock_client.get.call_count == 2
            # First call should be for search
            args, kwargs = mock_client.get.call_args_list[0]
            assert args[0] == "https://en.wikipedia.org/w/api.php"
            assert kwargs["params"]["srsearch"] == "python"
            assert kwargs["params"]["srlimit"] == 2
            
            # Second call should be for extracts
            args, kwargs = mock_client.get.call_args_list[1]
            assert args[0] == "https://en.wikipedia.org/w/api.php"
            assert kwargs["params"]["pageids"] == "123|456"
            
            # Verify result structure
            assert len(result["results"]) == 2
            assert result["results"][0]["title"] == "Python (programming language)"
            assert result["results"][0]["extract"] == "Python is a high-level programming language."
            assert result["results"][1]["title"] == "Python (genus)"
            assert result["results"][1]["extract"] == "Python is a genus of snakes."
    
    @pytest.mark.asyncio
    async def test_no_search_results(self):
        """Test handling of no search results."""
        # Create mock response objects
        response = AsyncMock()
        response.status_code = 200
        
        # Important: Set json() to return an awaitable that resolves to our test data
        empty_data = {
            "query": {
                "search": []
            }
        }
        response.json = AsyncMock(return_value=empty_data)
        
        # Create mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = response
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = mock_client
        
        # Patch the AsyncClient constructor to return our mock context manager
        with patch('httpx.AsyncClient', return_value=async_cm):
            result = await wikipedia_search("nonexistent_query_that_should_return_nothing")
        
            # Verify only one request was made (no extract request if no search results)
            assert mock_client.get.call_count == 1
            
            # Verify result structure indicating no results
            assert len(result["results"]) == 0
            assert "message" in result
            assert result["message"] == "No articles found"
    
    @pytest.mark.asyncio
    async def test_api_error(self):
        """Test handling of API errors."""
        # Create mock response objects
        response = AsyncMock()
        response.status_code = 500
        
        # Create mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = response
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = mock_client
        
        # Patch the AsyncClient constructor to return our mock context manager
        with patch('httpx.AsyncClient', return_value=async_cm):
            with pytest.raises(Exception) as exc_info:
                await wikipedia_search("python")
            
            assert "Wikipedia API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_limit_validation(self):
        """Test that limit parameter is properly validated and constrained."""
        # Create mock response objects
        response = AsyncMock()
        response.status_code = 200
        
        # Important: Set json() to return an awaitable that resolves to our test data
        empty_data = {"query": {"search": []}}
        response.json = AsyncMock(return_value=empty_data)
        
        # Create mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = response
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = mock_client
        
        # Patch the AsyncClient constructor to return our mock context manager
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Test with limit too low
            await wikipedia_search("python", limit=0)
            args, kwargs = mock_client.get.call_args
            assert kwargs["params"]["srlimit"] == 1
            
            # Reset mock
            mock_client.get.reset_mock()
            
            # Test with limit too high
            await wikipedia_search("python", limit=10)
            args, kwargs = mock_client.get.call_args
            assert kwargs["params"]["srlimit"] == 5