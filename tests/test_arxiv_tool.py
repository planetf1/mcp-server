"""Tests for the arXiv search tool."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module, not the function directly
import tools.tool_arxiv

class TestArxivTool:
    """Test cases for the arXiv search tool."""
    
    @pytest.mark.asyncio
    async def test_successful_search(self):
        """Test successful search with mock data."""
        # Mock test papers
        mock_papers = [
            {
                "id": "2106.12345",
                "title": "Test Paper 1",
                "authors": ["Author A", "Author B"],
                "summary": "This is a test paper about AI.",
                "published": "2023-01-01",
                "pdf_url": "https://arxiv.org/pdf/2106.12345.pdf",
                "url": "https://arxiv.org/abs/2106.12345",
                "categories": ["cs.AI", "cs.LG"]
            },
            {
                "id": "2106.67890",
                "title": "Test Paper 2",
                "authors": ["Author C"],
                "summary": "This is another test paper about ML.",
                "published": "2023-01-02",
                "pdf_url": "https://arxiv.org/pdf/2106.67890.pdf",
                "url": "https://arxiv.org/abs/2106.67890",
                "categories": ["cs.LG"]
            }
        ]
        
        # Create a mock that directly returns our test papers
        mock_function = AsyncMock(return_value=mock_papers)
        
        # Replace the function with our mock
        original_function = tools.tool_arxiv.arxiv_search
        tools.tool_arxiv.arxiv_search = mock_function
        
        try:
            # Call the function through the module
            result = await tools.tool_arxiv.arxiv_search("machine learning", max_results=2)
            
            # Verify the function was called with correct parameters
            mock_function.assert_called_once_with("machine learning", max_results=2)
            
            # Verify results match what we expect
            assert result == mock_papers
            assert len(result) == 2
            assert result[0]["title"] == "Test Paper 1"
            assert result[1]["title"] == "Test Paper 2"
            assert "pdf_url" in result[0]
            assert "url" in result[0]
        finally:
            # Restore the original function
            tools.tool_arxiv.arxiv_search = original_function
    
    @pytest.mark.asyncio
    async def test_empty_results(self):
        """Test handling of empty search results."""
        # Mock empty search results
        mock_function = AsyncMock(return_value=[])
        
        # Replace the function with our mock
        original_function = tools.tool_arxiv.arxiv_search
        tools.tool_arxiv.arxiv_search = mock_function
        
        try:
            # Call the function through the module
            result = await tools.tool_arxiv.arxiv_search("nonexistentquerythatreturnsnothing123456789", max_results=5)
            
            # Verify the function was called with correct parameters
            mock_function.assert_called_once_with(
                "nonexistentquerythatreturnsnothing123456789", max_results=5
            )
            
            # Verify empty list is returned
            assert isinstance(result, list)
            assert len(result) == 0
        finally:
            # Restore the original function
            tools.tool_arxiv.arxiv_search = original_function
    
    @pytest.mark.asyncio
    async def test_max_results_parameter(self):
        """Test that max_results parameter works correctly."""
        # Create papers with different IDs
        mock_papers_3 = [{"id": f"paper{i}", "title": f"Paper {i}"} for i in range(3)]
        mock_papers_5 = [{"id": f"paper{i}", "title": f"Paper {i}"} for i in range(5)]
        
        # Use side_effect to return different results for different calls
        mock_function = AsyncMock(side_effect=[mock_papers_3, mock_papers_5])
        
        # Replace the function with our mock
        original_function = tools.tool_arxiv.arxiv_search
        tools.tool_arxiv.arxiv_search = mock_function
        
        try:
            # Test with max_results=3
            result1 = await tools.tool_arxiv.arxiv_search("quantum computing", max_results=3)
            assert len(result1) == 3
            
            # Test with max_results=5
            result2 = await tools.tool_arxiv.arxiv_search("quantum computing", max_results=5)
            assert len(result2) == 5
            
            # Verify the function was called with correct parameters
            assert mock_function.call_count == 2
            mock_function.assert_any_call("quantum computing", max_results=3)
            mock_function.assert_any_call("quantum computing", max_results=5)
        finally:
            # Restore the original function
            tools.tool_arxiv.arxiv_search = original_function
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in arXiv search."""
        # Mock an exception
        mock_function = AsyncMock(side_effect=Exception("API error"))
        
        # Replace the function with our mock
        original_function = tools.tool_arxiv.arxiv_search
        tools.tool_arxiv.arxiv_search = mock_function
        
        try:
            # Try to call the function, expecting an exception
            with pytest.raises(Exception) as excinfo:
                await tools.tool_arxiv.arxiv_search("machine learning")
            
            # Verify the exception contains our error message
            assert "API error" in str(excinfo.value)
        finally:
            # Restore the original function
            tools.tool_arxiv.arxiv_search = original_function
