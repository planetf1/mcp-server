"""Tests for GitHub API tools."""
import pytest
import sys
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock
import base64

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_github import (
    github_get_file, 
    github_list_issues, 
    github_create_issue, 
    github_list_pull_requests,
    github_search_code,
    github_user_activity,
    GitHubToolError
)

class TestGitHubTools:
    """Test cases for GitHub API tools."""
    
    @pytest.mark.asyncio
    @pytest.fixture(autouse=True)
    async def setup(self, mock_httpx_client, github_token_env):
        """Set up test environment."""
        self.client, self.response = mock_httpx_client
        
        # Patch httpx.AsyncClient to return our mock
        patcher = patch('httpx.AsyncClient', return_value=self.client)
        patcher.start()
        yield
        patcher.stop()

    @pytest.mark.asyncio
    async def test_github_get_file(self):
        """Test retrieving a file from GitHub."""
        # Setup mock response
        content = "This is test content"
        encoded_content = base64.b64encode(content.encode()).decode()
        self.response.json.return_value = {
            "type": "file",
            "content": encoded_content,
            "name": "test.txt",
            "path": "test/test.txt",
            "sha": "abc123",
            "size": len(content),
            "html_url": "https://github.com/testuser/testrepo/blob/main/test/test.txt"
        }
        
        result = await github_get_file("testuser/testrepo", "test/test.txt")
        
        # Verify client was called with correct parameters
        self.client.get.assert_called_once()
        args, kwargs = self.client.get.call_args
        assert args[0] == "https://api.github.com/repos/testuser/testrepo/contents/test/test.txt"
        assert kwargs["params"] == {"ref": "main"}
        
        # Verify response content
        assert result["content"] == content
        assert result["name"] == "test.txt"
        assert result["path"] == "test/test.txt"
    
    @pytest.mark.asyncio
    async def test_github_get_file_not_found(self):
        """Test handling of file not found."""
        self.response.status_code = 404
        
        result = await github_get_file("testuser/testrepo", "nonexistent.txt")
        
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_github_get_file_not_a_file(self):
        """Test handling when path is not a file."""
        self.response.status_code = 200
        self.response.json.return_value = {"type": "dir"}
        
        result = await github_get_file("testuser/testrepo", "dir")
        
        assert "error" in result
        assert "not a file" in result["error"].lower() or "file" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_github_list_issues(self):
        """Test listing issues from a repository."""
        self.response.json.return_value = [
            {
                "number": 1,
                "title": "Test Issue",
                "state": "open",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
                "html_url": "https://github.com/testuser/testrepo/issues/1",
                "user": {"login": "testuser"},
                "labels": [{"name": "bug"}],
                "body": "This is a test issue"
            }
        ]
        
        result = await github_list_issues("testuser/testrepo")
        
        # Verify client was called correctly
        self.client.get.assert_called_once()
        args, kwargs = self.client.get.call_args
        assert args[0] == "https://api.github.com/repos/testuser/testrepo/issues"
        assert kwargs["params"] == {"state": "open"}
        
        # Verify response content
        assert len(result) == 1
        assert result[0]["number"] == 1
        assert result[0]["title"] == "Test Issue"
        assert result[0]["labels"] == ["bug"]
    
    @pytest.mark.asyncio
    async def test_github_create_issue(self):
        """Test creating an issue in a repository."""
        self.response.status_code = 201
        self.response.json.return_value = {
            "number": 2,
            "title": "New Issue",
            "html_url": "https://github.com/testuser/testrepo/issues/2",
            "state": "open",
            "created_at": "2023-01-03T00:00:00Z"
        }
        
        result = await github_create_issue(
            "testuser/testrepo", 
            "New Issue", 
            "This is a new issue", 
            ["bug", "enhancement"]
        )
        
        # Verify client was called correctly
        self.client.post.assert_called_once()
        args, kwargs = self.client.post.call_args
        assert args[0] == "https://api.github.com/repos/testuser/testrepo/issues"
        assert kwargs["json"]["title"] == "New Issue"
        assert kwargs["json"]["body"] == "This is a new issue"
        assert kwargs["json"]["labels"] == ["bug", "enhancement"]
        
        # Verify response content
        assert result["number"] == 2
        assert result["title"] == "New Issue"
        assert result["state"] == "open"
    
    @pytest.mark.asyncio
    async def test_github_list_pull_requests(self):
        """Test listing pull requests from a repository."""
        self.response.json.return_value = [
            {
                "number": 3,
                "title": "Test PR",
                "state": "open",
                "created_at": "2023-01-04T00:00:00Z",
                "updated_at": "2023-01-05T00:00:00Z",
                "html_url": "https://github.com/testuser/testrepo/pull/3",
                "user": {"login": "testuser"},
                "head": {"ref": "feature-branch"},
                "base": {"ref": "main"}
            }
        ]
        
        result = await github_list_pull_requests("testuser/testrepo")
        
        # Verify client was called correctly
        self.client.get.assert_called_once()
        args, kwargs = self.client.get.call_args
        assert args[0] == "https://api.github.com/repos/testuser/testrepo/pulls"
        assert kwargs["params"] == {"state": "open"}
        
        # Verify response content
        assert len(result) == 1
        assert result[0]["number"] == 3
        assert result[0]["title"] == "Test PR"
        assert result[0]["head"] == "feature-branch"
        assert result[0]["base"] == "main"
    
    @pytest.mark.asyncio
    async def test_github_search_code(self):
        """Test searching for code on GitHub."""
        self.response.json.return_value = {
            "total_count": 1,
            "items": [
                {
                    "repository": {"full_name": "testuser/testrepo"},
                    "path": "src/example.py",
                    "name": "example.py",
                    "html_url": "https://github.com/testuser/testrepo/blob/main/src/example.py"
                }
            ]
        }
        
        result = await github_search_code("test", "testuser/testrepo")
        
        # Verify client was called correctly
        self.client.get.assert_called_once()
        args, kwargs = self.client.get.call_args
        assert args[0] == "https://api.github.com/search/code"
        assert kwargs["params"]["q"] == "test repo:testuser/testrepo"
        
        # Verify response content
        assert result["total_count"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["repository"] == "testuser/testrepo"
        assert result["items"][0]["path"] == "src/example.py"
    
    @pytest.mark.asyncio
    async def test_github_user_activity(self):
        """Test retrieving user activity."""
        # We need to create side effects for multiple calls
        # Reset the mock and create side effects for the sequence of calls
        self.client.get.reset_mock()
        
        # Setup sequence of responses
        user_response = AsyncMock(status_code=200)
        user_response.json.return_value = {"login": "testuser"}
        
        issues_response = AsyncMock(status_code=200)
        issues_response.json.return_value = {"items": [
            {
                "title": "Issue Title",
                "html_url": "https://github.com/testuser/testrepo/issues/1",
                "created_at": "2023-01-01T00:00:00Z",
                "repository_url": "https://api.github.com/repos/testuser/testrepo"
            }
        ]}
        
        prs_response = AsyncMock(status_code=200)
        prs_response.json.return_value = {"items": [
            {
                "title": "PR Title",
                "html_url": "https://github.com/testuser/testrepo/pull/2",
                "created_at": "2023-01-02T00:00:00Z",
                "repository_url": "https://api.github.com/repos/testuser/testrepo",
                "state": "open",
                "pull_request": {"url": "https://api.github.com/repos/testuser/testrepo/pulls/2"}
            }
        ]}
        
        pr_detail_response = AsyncMock(status_code=200)
        pr_detail_response.json.return_value = {"merged": True}
        
        comments_response = AsyncMock(status_code=200)
        comments_response.json.return_value = {"items": [
            {
                "title": "Commented Issue",
                "html_url": "https://github.com/testuser/testrepo/issues/3",
                "updated_at": "2023-01-03T00:00:00Z",
                "repository_url": "https://api.github.com/repos/testuser/testrepo"
            }
        ]}
        
        reviews_response = AsyncMock(status_code=200)
        reviews_response.json.return_value = {"items": [
            {
                "title": "Reviewed PR",
                "html_url": "https://github.com/testuser/testrepo/pull/4",
                "updated_at": "2023-01-04T00:00:00Z",
                "repository_url": "https://api.github.com/repos/testuser/testrepo"
            }
        ]}
        
        # Setup side effects
        self.client.get.side_effect = [
            user_response,
            issues_response,
            prs_response,
            pr_detail_response,
            comments_response,
            reviews_response
        ]
        
        result = await github_user_activity("testuser")
        
        # Verify result structure
        assert result["username"] == "testuser"
        assert "period" in result
        assert result["summary"]["issues_opened_count"] == 1
        assert result["summary"]["prs_opened_count"] == 1
        assert result["summary"]["prs_merged_count"] == 1
        assert result["summary"]["issues_commented_count"] == 1
        assert result["summary"]["pr_reviews_count"] == 1
