"""Tests for the calculator tool."""
import pytest
import sys
import os

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_calculator import calculator

class TestCalculatorTool:
    """Test cases for the calculator tool."""
    
    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test that basic mathematical operations work correctly."""
        # Addition
        result = await calculator("2 + 2")
        assert result["result"] == 4
        
        # Subtraction
        result = await calculator("10 - 5")
        assert result["result"] == 5
        
        # Multiplication
        result = await calculator("6 * 7")
        assert result["result"] == 42
        
        # Division
        result = await calculator("100 / 5")
        assert result["result"] == 20
        
        # Power
        result = await calculator("2 ** 8")
        assert result["result"] == 256
        
        # Modulo
        result = await calculator("10 % 3")
        assert result["result"] == 1
        
        # Order of operations
        result = await calculator("2 + 3 * 4")
        assert result["result"] == 14
        
        # Parentheses
        result = await calculator("(2 + 3) * 4")
        assert result["result"] == 20
    
    @pytest.mark.asyncio
    async def test_math_functions(self):
        """Test that mathematical functions work correctly."""
        # Square root
        result = await calculator("sqrt(16)")
        assert result["result"] == 4
        
        # Sine
        result = await calculator("sin(0)")
        assert result["result"] == 0
        
        # Cosine
        result = await calculator("cos(0)")
        assert result["result"] == 1
        
        # Tangent
        result = await calculator("tan(0)")
        assert result["result"] == 0
    
    @pytest.mark.asyncio
    async def test_complex_expressions(self):
        """Test complex expressions with multiple operations."""
        result = await calculator("2 * (3 + 4) / 2 - 1")
        assert result["result"] == 6
        
        result = await calculator("sqrt(16) + sin(0) * 10")
        assert result["result"] == 4
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test that errors are handled gracefully."""
        # Division by zero
        result = await calculator("1 / 0")
        assert "error" in result
        
        # Invalid syntax
        result = await calculator("2 +* 3")
        assert "error" in result
        
        # Unsupported function
        result = await calculator("log(10)")
        assert "error" in result
        
        # Empty expression
        result = await calculator("")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_caret_operator(self):
        """Test that the caret operator is converted to power."""
        result = await calculator("2 ^ 3")
        assert result["result"] == 8
