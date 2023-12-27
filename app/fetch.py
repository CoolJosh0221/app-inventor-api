import aiohttp
from urllib.parse import urlencode

BASE_URL = "https://api.open-meteo.com/v1"
session = aiohttp.ClientSession()


async def get_response(url: str):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return 200, data
            else:
                return response.status, {"error": "Failed to fetch weather data"}
    except Exception as e:
        return 500, {"error": f"Failed to fetch weather data: {str(e)}"}


def validate_coordinates(lat: float, lon: float):
    if not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= lon <= 180):
        raise ValueError("Longitude must be between -180 and 180")


async def fetch_daily_weather_forecast(lat: float, lon: float):
    try:
        validate_coordinates(lat, lon)
    except ValueError as e:
        return 400, {"error": str(e)}

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "timeformat": "unixtime",
    }
    url = f"{BASE_URL}/forecast?{urlencode(params)}"

    try:
        response = await get_response(url)
        return response
    except Exception as e:
        return 500, {"error": f"Failed to fetch weather data: {str(e)}"}


async def fetch_hourly_weather_forecast(lat: float, lon: float):
    try:
        validate_coordinates(lat, lon)
    except ValueError as e:
        return 400, {"error": str(e)}

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "cloud_cover,temperature_2m,rain,showers,snowfall,uv_index",
        "timezone": "auto",
        "forecast_days": 1,
        "timeformat": "unixtime",
    }
    url = f"{BASE_URL}/forecast?{urlencode(params)}"

    try:
        response = await get_response(url)
        return response
    except Exception as e:
        return 500, {"error": f"Failed to fetch weather data: {str(e)}"}


async def fetch_air_quality_forecast(lat: float, lon: float):
    try:
        validate_coordinates(lat, lon)
    except ValueError as e:
        return 400, {"error": str(e)}

    params = {"latitude": lat, "longitude": lon, "hourly": "pm10,pm2_5", "timeformat": "unixtime"}
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?{urlencode(params)}"

    try:
        response = await get_response(url)
        return response
    except Exception as e:
        return 500, {"error": f"Failed to fetch weather data: {str(e)}"}
