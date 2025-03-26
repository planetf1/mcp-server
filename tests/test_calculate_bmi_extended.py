"""Extended tests for the BMI calculator tool."""
import pytest
import sys
import os
import math

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_calculate_bmi import calculate_bmi

class TestBMICalculatorExtended:
    """Extended tests for the BMI calculator tool."""
    
    def test_bmi_categories(self):
        """Test that BMI values fall into the correct categories."""
        # Test underweight (BMI < 18.5)
        bmi = calculate_bmi(50, 1.7)  # BMI ≈ 17.3
        assert bmi < 18.5
        
        # Test normal weight (18.5 <= BMI < 25)
        bmi = calculate_bmi(65, 1.75)  # BMI ≈ 21.2
        assert 18.5 <= bmi < 25
        
        # Test overweight (25 <= BMI < 30)
        bmi = calculate_bmi(85, 1.8)  # BMI ≈ 26.2
        assert 25 <= bmi < 30
        
        # Test obese (BMI >= 30)
        bmi = calculate_bmi(100, 1.75)  # BMI ≈ 32.7
        assert bmi >= 30
    
    def test_extreme_values(self):
        """Test with extreme but valid values."""
        # Test with extremely low but valid weight
        bmi = calculate_bmi(20, 1.8)  # Extremely low weight
        assert bmi == 20 / (1.8 ** 2)
        
        # Test with extremely high weight
        bmi = calculate_bmi(300, 1.8)  # Extremely high weight
        assert bmi == 300 / (1.8 ** 2)
        
        # Test with extremely low height
        bmi = calculate_bmi(70, 1.0)  # Extremely short height
        assert bmi == 70 / (1.0 ** 2)
        
        # Test with extremely high height
        bmi = calculate_bmi(70, 3.0)  # Extremely tall height
        assert bmi == 70 / (3.0 ** 2)
    
    def test_floating_point_precision(self):
        """Test floating point precision in BMI calculations."""
        # Test with typical values but with many decimal places
        bmi = calculate_bmi(70.123456, 1.7234567)
        expected_bmi = 70.123456 / (1.7234567 ** 2)
        assert math.isclose(bmi, expected_bmi, rel_tol=1e-9)
