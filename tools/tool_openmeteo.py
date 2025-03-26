"""
Weather forecast tool using the Open-Meteo API.
Free and open-source weather API with no API key required.
"""
import httpx
from typing import Dict, List, Optional, Any, Union
from mcp_instance import mcp

# Weather code mapping
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}

@mcp.tool()
async def openmeteo_forecast(location: str, days: int = 7) -> Dict[str, Any]:
    """
    Get a weather forecast for a location using Open-Meteo API
    
    Args:
        location: City name or location
        days: Number of forecast days (1-14)
        
    Returns:
        Weather forecast including daily temperature, precipitation, and weather conditions
    """
    # Validate days parameter
    if not (1 <= days <= 14):
        days = min(max(days, 1), 14)
    
    # Common function to handle API errors
    async def handle_api_error(response):
        if response.status_code != 200:
            return {"error": f"API error: {response.status_code}"}
        return None
    
    async with httpx.AsyncClient() as client:
        # First, geocode the location to get coordinates
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_response = await client.get(
            geocoding_url,
            params={
                "name": location,
                "count": 1,  # Get only the best match
                "language": "en",
                "format": "json"
            }
        )
        
        # Check for API errors
        error = await handle_api_error(geo_response)
        if error:
            return error
        
        geo_data = await geo_response.json()
        
        # Check if we got any results - handle both results formats
        results = []
        if isinstance(geo_data, list):
            results = geo_data
        elif isinstance(geo_data, dict) and "results" in geo_data:
            results = geo_data["results"]
            
        if not results:
            return {"error": f"Location not found: {location}"}
        
        # Get coordinates for the first (best) match
        place = results[0]
        latitude = place["latitude"]
        longitude = place["longitude"]
        
        # Get the full location name
        place_name = place["name"]
        country = place.get("country", "")
        full_location = f"{place_name}, {country}" if country else place_name
        
        # Now get the weather forecast
        forecast_url = "https://api.open-meteo.com/v1/forecast"
        forecast_response = await client.get(
            forecast_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": ["temperature_2m_max", "temperature_2m_min", 
                         "precipitation_sum", "weathercode"],
                "timezone": "auto",
                "forecast_days": days
            }
        )
        
        # Check for API errors
        error = await handle_api_error(forecast_response)
        if error:
            return error
        
        forecast_data = await forecast_response.json()
        
        # Process the forecast data into a more user-friendly format
        daily_data = []
        daily = forecast_data.get("daily", {})
        
        # Check if we have all required data
        if not daily or "time" not in daily:
            return {"error": "Invalid forecast data received"}
        
        # Create daily forecast entries
        for i, date in enumerate(daily["time"]):
            weather_code = daily.get("weathercode", [0] * len(daily["time"]))[i]
            weather_description = WEATHER_CODES.get(weather_code, "Unknown")
            
            daily_data.append({
                "date": date,
                "max_temp": daily.get("temperature_2m_max", [None] * len(daily["time"]))[i],
                "min_temp": daily.get("temperature_2m_min", [None] * len(daily["time"]))[i],
                "precipitation": daily.get("precipitation_sum", [None] * len(daily["time"]))[i],
                "weather_code": weather_code,
                "weather_description": weather_description
            })
        
        return {
            "location": full_location,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": forecast_data.get("timezone", "UTC"),
            "daily_forecast": daily_data
        }
