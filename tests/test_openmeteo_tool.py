"""Tests for the Open-Meteo weather tool."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_openmeteo import openmeteo_forecast

class TestOpenMeteoTool:
    """Test cases for the Open-Meteo weather tool."""
    
    @pytest.mark.asyncio
    async def test_successful_forecast(self, mock_httpx_client):
        """Test successful weather forecast with mock data."""
        client, response = mock_httpx_client
        
        # Mock geocoding response
        geocoding_data = [{
            "id": 12345,
            "name": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "country": "United States",
            "admin1": "New York"
        }]
        
        # Mock weather forecast response
        forecast_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "timezone": "America/New_York",
            "daily": {
                "time": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "temperature_2m_max": [10.5, 12.3, 9.8],
                "temperature_2m_min": [5.2, 6.7, 4.1],
                "precipitation_sum": [0.0, 5.2, 1.8],
                "weathercode": [0, 61, 80]
            }
        }
        
        # Configure response side effects
        response.json = AsyncMock()
        response.json.side_effect = [geocoding_data, forecast_data]
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            result = await openmeteo_forecast("New York", days=3)
            
            # Verify client was called correctly
            assert client.get.call_count == 2
            
            # Verify first call was for geocoding
            args, kwargs = client.get.call_args_list[0]
            assert "geocoding-api.open-meteo.com" in args[0]
            assert kwargs["params"]["name"] == "New York"
            
            # Verify second call was for forecast
            args, kwargs = client.get.call_args_list[1]
            assert "api.open-meteo.com" in args[0]
            assert kwargs["params"]["latitude"] == 40.7128
            assert kwargs["params"]["longitude"] == -74.0060
            assert kwargs["params"]["forecast_days"] == 3
            
            # Verify results are processed correctly
            assert result["location"] == "New York, United States"
            assert len(result["daily_forecast"]) == 3
            assert result["daily_forecast"][0]["date"] == "2023-01-01"
            assert result["daily_forecast"][1]["max_temp"] == 12.3
            assert result["daily_forecast"][2]["precipitation"] == 1.8
    
    @pytest.mark.asyncio
    async def test_location_not_found(self, mock_httpx_client):
        """Test handling of location not found error."""
        client, response = mock_httpx_client
        
        # Mock empty geocoding response
        response.json = AsyncMock(return_value=[])
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            result = await openmeteo_forecast("NonexistentLocation12345")
            
            # Verify error is returned correctly
            assert "error" in result
            assert "location not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_api_error(self, mock_httpx_client):
        """Test handling of API errors."""
        client, response = mock_httpx_client
        
        # Mock error response
        response.status_code = 500
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            result = await openmeteo_forecast("New York")
            
            # Verify error is returned correctly
            assert "error" in result
            assert "api error" in result["error"].lower() or "500" in result["error"]
    
    @pytest.mark.asyncio
    async def test_forecast_days_parameter(self, mock_httpx_client):
        """Test that forecast_days parameter is respected."""
        client, response = mock_httpx_client
        
        # Mock successful geocoding response
        geocoding_data = [{
            "name": "Berlin",
            "latitude": 52.5200,
            "longitude": 13.4050,
            "country": "Germany"
        }]
        
        # Mock forecast responses with different days
        forecast_data_7_days = {
            "daily": {
                "time": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", 
                         "2023-01-05", "2023-01-06", "2023-01-07"],
                "temperature_2m_max": [10, 11, 12, 13, 14, 15, 16],
                "temperature_2m_min": [5, 6, 7, 8, 9, 10, 11],
                "precipitation_sum": [0, 0, 0, 0, 0, 0, 0],
                "weathercode": [0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        # Configure response side effects
        response.json = AsyncMock()
        response.json.side_effect = [geocoding_data, forecast_data_7_days]
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Test with 7 days forecast
            result = await openmeteo_forecast("Berlin", days=7)
            
            # Verify forecast days parameter was passed correctly
            args, kwargs = client.get.call_args_list[1]
            assert kwargs["params"]["forecast_days"] == 7
            
            # Verify correct number of days in result
            assert len(result["daily_forecast"]) == 7
