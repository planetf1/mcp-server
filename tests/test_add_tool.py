"""Tests for the add tool."""
import pytest
import sys
import os

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_add import add

class TestAddTool:
    """Test cases for the add tool."""
    
    def test_basic_addition(self):
        """Test basic addition of two numbers."""
        result = add(3, 4)
        assert result == 7
        
        result = add(10, 20)
        assert result == 30
        
        result = add(0, 0)
        assert result == 0
    
    def test_negative_numbers(self):
        """Test addition with negative numbers."""
        result = add(-5, 10)
        assert result == 5
        
        result = add(-10, -20)
        assert result == -30
    
    def test_float_numbers(self):
        """Test addition with floating point numbers."""
        result = add(3.5, 2.5)
        assert result == 6.0
        
        # Test precision
        result = add(0.1, 0.2)
        assert abs(result - 0.3) < 1e-10
    
    def test_large_numbers(self):
        """Test addition with very large numbers."""
        result = add(10**15, 10**15)
        assert result == 2 * 10**15
        
        # Python can handle arbitrary large integers
        result = add(10**100, 10**100)
        assert result == 2 * 10**100
