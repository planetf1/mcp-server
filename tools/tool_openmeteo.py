import httpx
from mcp_instance import mcp

@mcp.tool()
async def openmeteo_weather(latitude: float, longitude: float, forecast_days: int = 1) -> dict:
    """
    Get weather data from Open-Meteo API
    
    Args:
        latitude: The latitude coordinate
        longitude: The longitude coordinate
        forecast_days: Number of days to forecast (1-7)
        
    Returns:
        Weather data including temperature, precipitation, etc.
    """
    if not (1 <= forecast_days <= 7):
        forecast_days = min(max(forecast_days, 1), 7)
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "forecast_days": forecast_days,
                "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weather_code"],
                "timezone": "auto"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Open-Meteo API error: {response.status_code} - {response.text}")
            
        return response.json()
