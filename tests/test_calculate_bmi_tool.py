"""Tests for the BMI calculator tool."""
import pytest
import sys
import os

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_calculate_bmi import calculate_bmi

class TestCalculateBmiTool:
    """Test cases for the BMI calculator tool."""
    
    def test_normal_bmi_calculation(self):
        """Test calculation of BMI with typical values."""
        # Normal weight example (BMI ~22)
        bmi = calculate_bmi(70, 1.8)
        assert round(bmi, 1) == 21.6
        
        # Underweight example (BMI ~17)
        bmi = calculate_bmi(50, 1.7)
        assert round(bmi, 1) == 17.3
        
        # Overweight example (BMI ~27)
        bmi = calculate_bmi(80, 1.72)
        assert round(bmi, 1) == 27.0
        
        # Obese example (BMI ~33)
        bmi = calculate_bmi(100, 1.75)
        assert round(bmi, 1) == 32.7
    
    def test_edge_cases(self):
        """Test edge cases with very low or high values."""
        # Very low weight
        bmi = calculate_bmi(30, 1.6)
        assert round(bmi, 1) == 11.7
        
        # Very high weight
        bmi = calculate_bmi(150, 1.9)
        assert round(bmi, 1) == 41.6
        
        # Very short height
        bmi = calculate_bmi(50, 1.4)
        assert round(bmi, 1) == 25.5
        
        # Very tall height
        bmi = calculate_bmi(100, 2.1)
        assert round(bmi, 1) == 22.7
    
    def test_error_cases(self):
        """Test that errors are raised for invalid inputs."""
        # Zero height should raise ZeroDivisionError
        with pytest.raises(ZeroDivisionError):
            calculate_bmi(70, 0)
        
        # Negative values are not realistic but should mathematically work
        # though they produce meaningless results
        bmi = calculate_bmi(-70, 1.8)
        assert bmi < 0
