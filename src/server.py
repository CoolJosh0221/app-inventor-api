import base64
import bisect
import pendulum
import os
import logging
import requests
import sys
from dotenv import load_dotenv
from notion_client import AsyncClient
from pprint import pprint
from io import BytesIO

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse

from .text_to_speech import generate
from .fetch import (
    fetch_daily_weather_forecast,
    fetch_hourly_weather_forecast,
    fetch_air_quality_forecast,
)

load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application stopped")


def lower_bound(arr, target):
    index = bisect.bisect_left(arr, target)
    if index < len(arr) and arr[index] == target:
        return index + 1
    elif index == 0:
        return 1
    else:
        return index


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/get_weather")
async def get_weather(
    lat: float = Query(..., title="Latitude", description="Latitude coordinate"),
    lon: float = Query(..., title="Longitude", description="Longitude coordinate"),
    cur_time: int = Query(default=..., title="Unix timestamp", description="Pass in current time"),
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
    timezone = daily_report["timezone"]
    unix_time = hourly_weather["time"]

    notify_umbrella = list(
        map(
            lambda x: x > 30,
            precipitation_probabilities,
        )
    )  # to notify user to bring umbrella
    notify_jacket = list(
        map(
            lambda x: x < 20,
            max_temperatures,
        )
    )  # notify user to bring jacket
    notify_sunscreen = list(
        map(
            lambda x: x >= 5,
            uv_index,
        )
    )
    normal_time = list(
        map(lambda x: pendulum.from_timestamp(x, timezone).strftime("%m/%d/%Y %H:%M"), unix_time)
    )

    additional_data_daily = {
        "notify_umbrella": notify_umbrella,
        "notify_jacket": notify_jacket,
    }

    additional_data_hourly = {
        "notify_sunscreen": notify_sunscreen,
    }

    hourly_weather.update(air_quality_report["hourly"])
    hourly_weather.update(additional_data_hourly)
    daily_weather.update(additional_data_daily)
    hourly_weather["normal_time"] = normal_time
    daily_report["hourly"] = hourly_report["hourly"]
    daily_report["hourly_units"] = hourly_report["hourly_units"]
    daily_report["now_time_index"] = lower_bound(daily_report['hourly']['time'], cur_time)

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


@app.get("/auth/notion/callback")
async def notion_callback(
    code: str = Query(
        ...,
        title="Authentication Code",
        description="Authentication Code",
    ),
    state: str = Query(..., title="State", description="State", required=False),
):
    client_id = os.environ["OAUTH_CLIENT_ID"]
    client_secret = os.environ["OAUTH_CLIENT_SECRET"]
    encoded = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    url = 'https://api.notion.com/v1/oauth/token'
    headers = {
        'Authorization': f'Basic {encoded}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28',
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"https://adelaide-clownfish-xqag.2.sg-1.fl0.io/auth/notion/callback",
    }
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    return await process_database(response_data)


async def process_database(response_data):
    pprint(response_data)
    token = response_data['access_token']
    database_id = response_data['duplicated_template_id']
    notion = AsyncClient(token)
    database = await notion.databases.retrieve(database_id=database_id)
    pprint(database)
    return database

    # pprint(response_data)
    # pageId = '231de349-3882-4bce-bc05-d9dc362b7ea4'
    # url = f'https://api.notion.com/v1/pages/{pageId}'
    # headers = {
    #     'Notion-Version': '2022-06-28',
    #     'Authorization': f'Bearer {response_data["access_token"]}',
    # }
    # response = requests.get(url=url, headers=headers)
    # response_data2 = response.json()
    # return response_data2
