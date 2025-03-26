"""Tests for the long task tool."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_long_task import long_task

class TestLongTaskTool:
    """Test cases for the long task tool."""
    
    @pytest.mark.asyncio
    async def test_long_task_processing(self, mock_context):
        """Test that long task processes files with progress updates."""
        # Set up test data
        files = ["file1.txt", "file2.txt", "file3.txt"]
        
        # Call the function
        result = await long_task(files, mock_context)
        
        # Verify that context methods were called correctly
        assert mock_context.info.call_count == 3
        assert mock_context.report_progress.call_count == 3
        assert mock_context.read_resource.call_count == 3
        
        # Check first call arguments for each method
        mock_context.info.assert_any_call("Processing file1.txt")
        mock_context.report_progress.assert_any_call(0, 3)
        mock_context.read_resource.assert_any_call("file://file1.txt")
        
        # Check second call arguments
        mock_context.info.assert_any_call("Processing file2.txt")
        mock_context.report_progress.assert_any_call(1, 3)
        mock_context.read_resource.assert_any_call("file://file2.txt")
        
        # Check third call arguments
        mock_context.info.assert_any_call("Processing file3.txt")
        mock_context.report_progress.assert_any_call(2, 3)
        mock_context.read_resource.assert_any_call("file://file3.txt")
        
        # Verify the result
        assert result == "Processing complete"
    
    @pytest.mark.asyncio
    async def test_empty_file_list(self, mock_context):
        """Test that long task handles empty file list gracefully."""
        # Call with empty list
        result = await long_task([], mock_context)
        
        # Verify no processing was done
        assert mock_context.info.call_count == 0
        assert mock_context.report_progress.call_count == 0
        assert mock_context.read_resource.call_count == 0
        
        # Verify the result
        assert result == "Processing complete"
