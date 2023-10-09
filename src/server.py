from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from icecream import ic

from fetch import (
    fetch_daily_weather_forecast,
    fetch_hourly_weather_forecast,
    fetch_air_quality_forecast,
)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/get_weather")
async def get_weather(
    lat: float = Query(..., title="Latitude", description="Latitude coordinate"),
    lon: float = Query(..., title="Longitude", description="Longitude coordinate"),
):
    # JSON data
    daily_report = await fetch_daily_weather_forecast(lat, lon)
    hourly_report = await fetch_hourly_weather_forecast(lat, lon)
    air_quality_report = await fetch_air_quality_forecast(lat, lon)
    # Accessing daily weather data
    hourly_weather = hourly_report["hourly"]
    daily_weather = daily_report['daily']
    max_temperatures = daily_weather['temperature_2m_max']
    precipitation_probabilities = daily_weather['precipitation_probability_max']
    uv_index = hourly_report['hourly']['uv_index']

    notify_umbrella = map(
        lambda x: x > 30,
        precipitation_probabilities,
    )  # to notify user to bring umbrella
    notify_jacket = map(
        lambda x: x < 20,
        max_temperatures,
    )  # notify user to bring jacket
    notify_sunscreen = map(
        lambda x: x >= 5,
        uv_index,
    )

    additional_data_daily = {
        "notify_umbrella": list(notify_umbrella),
        "notify_jacket": list(notify_jacket),
    }

    additional_data_hourly = {
        "notify_sunscreen": list(notify_sunscreen),
    }

    hourly_weather.update(air_quality_report["hourly"])
    hourly_weather.update(additional_data_hourly)
    daily_weather.update(additional_data_daily)
    daily_report["hourly"] = hourly_report["hourly"]
    daily_report["hourly_units"] = hourly_report["hourly_units"]

    ic(daily_report)
    return daily_report
