"""Tests for the fetch weather tool."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_fetch_weather import fetch_weather

class TestFetchWeatherTool:
    """Test cases for the fetch weather tool."""
    
    @pytest.mark.asyncio
    async def test_successful_weather_fetch(self, mock_httpx_client):
        """Test successful weather fetch with mock data."""
        client, response = mock_httpx_client
        
        # Mock successful weather response
        weather_data = {
            "weather": [{"description": "clear sky", "icon": "01d"}],
            "main": {
                "temp": 25.5,
                "feels_like": 26.0,
                "temp_min": 24.0,
                "temp_max": 27.0,
                "humidity": 65
            },
            "wind": {"speed": 5.2},
            "name": "New York"
        }
        response.json = AsyncMock(return_value=weather_data)
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            result = await fetch_weather("New York")
            
            # Verify client was called correctly
            assert client.get.call_count == 1
            
            # Extract call arguments
            args, kwargs = client.get.call_args
            assert "api.openweathermap.org" in args[0]
            assert kwargs["params"]["q"] == "New York"
            
            # Verify results are processed correctly
            assert result["location"] == "New York"
            assert result["temperature"] == 25.5
            assert result["description"] == "clear sky"
            assert result["humidity"] == 65
            assert result["wind_speed"] == 5.2
    
    @pytest.mark.asyncio
    async def test_location_not_found(self, mock_httpx_client):
        """Test handling of location not found error."""
        client, response = mock_httpx_client
        
        # Mock a 404 not found response
        response.status_code = 404
        response.json = AsyncMock(return_value={"cod": "404", "message": "city not found"})
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            result = await fetch_weather("NonexistentCity12345")
            
            # Verify error is returned correctly
            assert "error" in result
            assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_api_key_error(self, mock_httpx_client):
        """Test handling of invalid API key error."""
        client, response = mock_httpx_client
        
        # Mock an unauthorized response
        response.status_code = 401
        response.json = AsyncMock(return_value={"cod": 401, "message": "Invalid API key"})
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            result = await fetch_weather("London")
            
            # Verify error is returned correctly
            assert "error" in result
            assert "api key" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_different_units(self, mock_httpx_client):
        """Test fetching weather with different units."""
        client, response = mock_httpx_client
        
        # Mock successful weather response
        response.json = AsyncMock(return_value={
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 20.0},
            "name": "London"
        })
        
        # Create a mock context manager
        async_cm = AsyncMock()
        async_cm.__aenter__.return_value = client
        
        # Patch the AsyncClient constructor
        with patch('httpx.AsyncClient', return_value=async_cm):
            # Test with imperial units
            await fetch_weather("London", units="imperial")
            args, kwargs = client.get.call_args
            assert kwargs["params"]["units"] == "imperial"
            
            # Reset mock
            client.get.reset_mock()
            
            # Test with metric units
            await fetch_weather("London", units="metric")
            args, kwargs = client.get.call_args
            assert kwargs["params"]["units"] == "metric"
