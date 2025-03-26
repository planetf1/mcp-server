"""Tests for the echo tool."""
import pytest
import sys
import os

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_echo_tool import echo

class TestEchoTool:
    """Test cases for the echo tool."""
    
    @pytest.mark.asyncio
    async def test_basic_echo(self):
        """Test basic echo functionality."""
        # Test with a simple string
        result = await echo("Hello, world!")
        assert result == "Hello, world!"
        
        # Test with empty string
        result = await echo("")
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test echo with special characters."""
        # Test with special characters
        result = await echo("!@#$%^&*()_+{}[]|\\:;\"'<>,.?/")
        assert result == "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/"
        
        # Test with Unicode characters
        result = await echo("こんにちは 你好 안녕하세요")
        assert result == "こんにちは 你好 안녕하세요"
    
    @pytest.mark.asyncio
    async def test_multiline_text(self):
        """Test echo with multiline text."""
        # Test with multiline string
        multiline = """Line 1
Line 2
Line 3"""
        result = await echo(multiline)
        assert result == multiline
    
    @pytest.mark.asyncio
    async def test_long_text(self):
        """Test echo with very long text."""
        # Create a really long string
        long_text = "A" * 10000
        result = await echo(long_text)
        assert result == long_text
        assert len(result) == 10000
