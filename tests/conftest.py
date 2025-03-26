"""Common fixtures and configuration for pytest tests."""
import os
import json
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.server.fastmcp import Context

# Mock MCP decorators, Context, and other objects
class MockMCP:
    def tool(self):
        def wrapper(func):
            return func
        return wrapper

@pytest.fixture
def mock_mcp():
    """Provide a mock MCP instance for testing tools."""
    return MockMCP()

@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.AsyncClient for testing."""
    client = AsyncMock()
    response = AsyncMock()
    
    # Ensure status_code is an integer, not a mock
    # Set the default to 200 for successful requests
    response.status_code = 200
    
    client.get.return_value = response
    client.post.return_value = response
    response.json = AsyncMock(return_value={})  # Use AsyncMock for json method
    return client, response

@pytest.fixture
def mock_context():
    """Create a mock Context object for testing long running tasks."""
    ctx = AsyncMock(spec=Context)
    # All these methods need to return awaitable objects
    ctx.send_progress = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.read_resource = AsyncMock(return_value=(b"test data", "text/plain"))
    ctx.info = AsyncMock()
    return ctx

@pytest.fixture
def github_token_env():
    """Set GitHub token environment variable for tests."""
    original = os.environ.get("GITHUB_TOKEN")
    os.environ["GITHUB_TOKEN"] = "test_github_token"
    yield
    if original is None:
        del os.environ["GITHUB_TOKEN"]
    else:
        os.environ["GITHUB_TOKEN"] = original
