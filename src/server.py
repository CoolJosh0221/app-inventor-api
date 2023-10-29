import os
from io import BytesIO

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from icecream import ic


from .text_to_speech import generate
from .fetch import (
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


# @app.get("/callback")
# async def callback(
#     code: str = Query(..., title="Authentication Code", description="Authentication Code"),
# ):
#     token = id_token.fetch_id_token(requests.Request(), code=code)

#     # Use the access token to make requests to the Google Calendar API
#     response = requests.get(
#         "https://www.googleapis.com/calendar/v3/events",
#         headers={"Authorization": f"Bearer {token}"},
#     )
#     events = response.json()

#     return events


@app.get("/audio")
async def get_audio(
    message: str = Query(..., title="Message", description="Message"),
    lang: str = Query(..., title="Language", description="Language"),
):
    file_name = generate(message, lang)
    file_path = os.path.join('audio', file_name)

    with open(file_path, 'rb') as file:
        file_contents = file.read()

    os.remove(file_path)

    return StreamingResponse(BytesIO(file_contents), media_type="audio/mpeg")
