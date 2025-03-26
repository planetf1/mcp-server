"""
Weather fetching tool using OpenWeatherMap API.
"""
import os
import httpx
from mcp_instance import mcp

@mcp.tool()
async def fetch_weather(location: str, units: str = "metric") -> dict:
    """
    Fetch current weather data for a location.
    
    Args:
        location: City name or location
        units: Temperature unit (metric, imperial, standard)
        
    Returns:
        Weather information including temperature, conditions, humidity and wind speed
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY", "dummy_key_for_testing")
    
    # Validate units parameter
    if units not in ["metric", "imperial", "standard"]:
        units = "metric"  # Default to metric if invalid
    
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            base_url,
            params={
                "q": location,
                "appid": api_key,
                "units": units
            }
        )
        
        # Handle error responses
        if response.status_code != 200:
            try:
                error_data = await response.json()
                error_message = error_data.get("message", f"API Error: {response.status_code}")
            except:
                error_message = f"API Error: {response.status_code}"
                
            return {"error": error_message}
        
        # Parse successful response
        data = await response.json()
        
        # Format the response
        return {
            "location": data.get("name", location),
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "min_temp": data.get("main", {}).get("temp_min"),
            "max_temp": data.get("main", {}).get("temp_max"),
            "humidity": data.get("main", {}).get("humidity"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "description": data.get("weather", [{}])[0].get("description", "Unknown"),
            "icon": data.get("weather", [{}])[0].get("icon"),
            "units": units
        }
