import requests


async def get_response(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return {"error": "Failed to fetch weather data"}


async def fetch_daily_weather_forecast(lat: float, lon: float):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto&timeformat=unixtime"

    response = await get_response(url)
    return response


async def fetch_hourly_weather_forecast(lat: float, lon: float):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=cloud_cover,temperature_2m,rain,showers,snowfall,uv_index&timezone=auto&forecast_days=1&timeformat=unixtime"

    response = await get_response(url)
    return response


async def fetch_air_quality_forecast(lat: float, lon: float):
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=pm10,pm2_5&timeformat=unixtime"

    response = await get_response(url)
    return response
