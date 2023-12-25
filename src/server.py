import aiofiles
import bisect
import pendulum
import os
import logging
from dotenv import load_dotenv
from notion_client import AsyncClient
from pprint import pprint
from io import BytesIO
from typing import List
from pathlib import Path

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
    hourly_unix_time = hourly_weather["time"]
    daily_unix_time = daily_weather["time"]

    notify_umbrella = [
        x > 30 for x in precipitation_probabilities
    ]  # to notify user to bring umbrella
    notify_jacket = [x < 20 for x in max_temperatures]  # notify user to bring jacket
    notify_sunscreen = [x >= 5 for x in uv_index]
    hourly_normal_time = [
        pendulum.from_timestamp(x, timezone).strftime("%m/%d/%Y %H:%M") for x in hourly_unix_time
    ]
    daily_normal_time = [
        pendulum.from_timestamp(x, timezone).strftime("%m/%d/%Y") for x in daily_unix_time
    ]

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
    daily_weather["normal_time"] = daily_normal_time
    hourly_weather["normal_time"] = hourly_normal_time
    daily_report["hourly"] = hourly_report["hourly"]
    daily_report["hourly_units"] = hourly_report["hourly_units"]
    daily_report["now_time_index"] = lower_bound(daily_report['hourly']['time'], cur_time)

    return daily_report


@app.get("/audio")
async def get_audio(
    message: str = Query(..., title="Message", description="Message"),
    lang: str = Query(..., title="Language", description="Language"),
    tld: str = Query('com', title="TLD", description="TLD"),
):
    current_dir = Path.cwd()
    logger.info(current_dir)
    await generate(message, lang, tld)
    file_path = os.path.join(current_dir, 'audio', 'output.mp3')

    async with aiofiles.open(file_path, 'rb') as file:
        return StreamingResponse(BytesIO(await file.read()), media_type="audio/mpeg")


@app.get(path="/process_database")
async def process_database(response_data):
    pprint(response_data)
    token = response_data['access_token']
    database_id = response_data['duplicated_template_id']
    # database_id = "3a7432d6-f52f-416e-96b1-d1139f109f7f"
    notion = AsyncClient(auth=token)
    database = await notion.databases.retrieve(database_id=database_id)
    pprint(database)

    pages = await notion.databases.query(database_id=database_id)
    pprint(pages)
    return pages


@app.get(path="/process_database_with_id")
async def process_database_with_id():
    token = os.environ["NOTION_TOKEN"]
    database_id = "19c342cf3da84bd5be5bf00a6559d316"

    notion = AsyncClient(auth=token)

    pages = await notion.databases.query(database_id=database_id)

    response = [
        {
            "object": page["object"],
            "url": page["url"],
            "title": page["properties"]["Name"]["title"][0]["plain_text"],
            "status": page["properties"]["Status"]["status"]["name"],
            "due_date": page["properties"]["Date"]["date"],
        }
        for page in pages["results"]
        if len(page["properties"]["Name"]["title"])
    ]

    return response


@app.get(path="/notion_checklist")
async def process_notion_checklist():
    token = os.environ["NOTION_TOKEN"]
    database_id = "3138c97a87704223a6868215a36585a6"

    notion = AsyncClient(auth=token)

    pages = await notion.databases.query(database_id=database_id)

    response = [
        {
            "object": page["object"],
            "url": page["url"],
            "title": page["properties"]["Name"]["title"][0]["plain_text"],
            "subject": page["properties"]["Subject"]["multi_select"][0]["name"]
            if page["properties"]["Subject"]["multi_select"]
            else None,
            "checkbox": page["properties"][""]["checkbox"],
        }
        for page in pages["results"]
        if len(page["properties"]["Name"]["title"])
    ]

    return response
