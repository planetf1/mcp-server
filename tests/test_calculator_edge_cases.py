"""Edge case tests for the calculator tool."""
import pytest
import sys
import os
import math

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_calculator import calculator

class TestCalculatorEdgeCases:
    """Test edge cases for the calculator tool."""
    
    @pytest.mark.asyncio
    async def test_very_large_numbers(self):
        """Test calculations with very large numbers."""
        # Test large exponentiation
        result = await calculator("10 ** 100")
        assert result["result"] == 10 ** 100
        
        # Test large multiplication
        result = await calculator("10 ** 50 * 10 ** 50")
        assert result["result"] == 10 ** 100
    
    @pytest.mark.asyncio
    async def test_float_precision(self):
        """Test floating point precision."""
        # Test precision in division
        result = await calculator("1 / 3")
        assert abs(result["result"] - 0.3333333333333333) < 1e-15
        
        # Test precision in math functions
        result = await calculator("sin(0.5)")
        assert abs(result["result"] - math.sin(0.5)) < 1e-15
    
    @pytest.mark.asyncio
    async def test_syntax_errors(self):
        """Test various syntax errors."""
        # Missing closing parenthesis
        result = await calculator("(2 + 3 * (4 - 1")
        assert "error" in result
        
        # Double operators
        result = await calculator("2 ++ 3")
        assert "error" in result
        
        # Unclosed quotes - this would be caught before evaluation
        result = await calculator("'test")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_security_concerns(self):
        """Test that potentially dangerous operations are blocked."""
        # Attempt to import modules
        result = await calculator("__import__('os').system('ls')")
        assert "error" in result
        
        # Attempt to access attributes
        result = await calculator("().__class__.__bases__[0].__subclasses__()")
        assert "error" in result
