"""Integration tests for GitHub API workflows."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
import base64

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_github import (
    github_get_file, 
    github_list_issues, 
    github_create_issue, 
    github_list_pull_requests,
    github_search_code,
    github_user_activity
)

class TestGitHubWorkflow:
    """Tests for complete GitHub workflows."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_httpx_client, github_token_env):
        """Set up test environment."""
        self.client, self.response = mock_httpx_client
    
    @pytest.mark.asyncio
    async def test_issue_workflow(self):
        """Test a complete workflow for finding and creating issues."""
        # Mock setup for different responses
        issue_list_response = AsyncMock()
        issue_list_response.status_code = 200
        issue_list_response.json = AsyncMock(return_value=[
            {
                "number": 1,
                "title": "Existing Issue",
                "state": "open",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "html_url": "https://github.com/testuser/testrepo/issues/1",
                "user": {"login": "testuser"},
                "labels": [{"name": "bug"}],
                "body": "This is an existing issue"
            }
        ])
        
        create_issue_response = AsyncMock()
        create_issue_response.status_code = 201
        create_issue_response.json = AsyncMock(return_value={
            "number": 2,
            "title": "New Issue",
            "html_url": "https://github.com/testuser/testrepo/issues/2",
            "state": "open",
            "created_at": "2023-01-02T00:00:00Z"
        })
        
        file_response = AsyncMock()
        file_response.status_code = 200
        file_content = "# Test File\nThis is a test file with an error on line 10."
        encoded_content = base64.b64encode(file_content.encode()).decode()
        file_response.json = AsyncMock(return_value={
            "type": "file",
            "content": encoded_content,
            "name": "README.md",
            "path": "README.md",
            "sha": "abc123",
            "size": len(file_content),
            "html_url": "https://github.com/testuser/testrepo/blob/main/README.md"
        })
        
        # Setup side effects sequence
        self.client.get.side_effect = [issue_list_response, file_response]
        self.client.post.return_value = create_issue_response
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = self.client
        
        # Workflow:
        # 1. Check existing issues
        # 2. Examine a file
        # 3. Create a new issue referencing the file
        
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Step 1: Check existing issues
            issues = await github_list_issues("testuser/testrepo")
            assert len(issues) == 1
            assert issues[0]["title"] == "Existing Issue"
            
            # Step 2: Examine a file
            file_result = await github_get_file("testuser/testrepo", "README.md")
            assert "This is a test file" in file_result["content"]
            
            # Step 3: Create a new issue referencing the file
            new_issue = await github_create_issue(
                "testuser/testrepo",
                "New Issue",
                f"Found a problem in [README.md]({file_result['url']}) on line 10.",
                ["bug"]
            )
            
            assert new_issue["number"] == 2
            assert new_issue["title"] == "New Issue"
            
            # Verify correct API calls were made
            assert self.client.get.call_count == 2
            assert self.client.post.call_count == 1
