import logging
from typing import Optional
import aiofiles
import pendulum
import os
from dotenv import load_dotenv
from notion_client import AsyncClient
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.tts import generate
from app.fetch import (
    fetch_daily_weather_forecast,
    fetch_hourly_weather_forecast,
    fetch_air_quality_forecast,
)

load_dotenv()

app = FastAPI()

logger = logging.getLogger("uvicorn")
token = os.getenv("NOTION_TOKEN")
notion = AsyncClient(auth=token)


@app.on_event("startup")
async def startup_event():
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application stopped")


def lower_bound(arr, target):
    left = 0
    right = len(arr)
    while left < right:
        mid = (left + right) // 2
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    return left + 1 if left < len(arr) and arr[left] == target else left


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/get_weather")
async def get_weather(
    lat: float = Query(..., title="Latitude", description="Latitude coordinate"),
    lon: float = Query(..., title="Longitude", description="Longitude coordinate"),
    cur_time: int = Query(default=..., title="Unix timestamp", description="Pass in current time"),
):
    response_code_daily, daily_report = await fetch_daily_weather_forecast(lat, lon)
    if response_code_daily != 200:
        logger.error(f"Error fetching daily weather data. Response code: {response_code_daily}")
        raise HTTPException(status_code=response_code_daily, detail=daily_report["error"])

    response_code_hourly, hourly_report = await fetch_hourly_weather_forecast(lat, lon)
    if response_code_hourly != 200:
        logger.error(f"Error fetching hourly weather data. Response code: {response_code_hourly}")
        raise HTTPException(status_code=response_code_hourly, detail=hourly_report["error"])

    response_code_air_quality, air_quality_report = await fetch_air_quality_forecast(lat, lon)
    if response_code_air_quality != 200:
        logger.error(f"Error fetching air quality data. Response code: {response_code_air_quality}")
        raise HTTPException(
            status_code=response_code_air_quality, detail=air_quality_report["error"]
        )

    hourly_weather = hourly_report["hourly"]
    daily_weather = daily_report["daily"]
    max_temperatures = daily_weather["temperature_2m_max"]
    precipitation_probabilities = daily_weather["precipitation_probability_max"]
    uv_index = hourly_report["hourly"]["uv_index"]
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

    hourly_weather.update(
        {
            **air_quality_report["hourly"],
            "notify_sunscreen": notify_sunscreen,
            "normal_time": hourly_normal_time,
        }
    )

    daily_weather.update(
        {
            "notify_umbrella": notify_umbrella,
            "notify_jacket": notify_jacket,
            "normal_time": daily_normal_time,
        }
    )

    daily_report.update(
        {
            "hourly": hourly_report["hourly"],
            "hourly_units": hourly_report["hourly_units"],
            "now_time_index": lower_bound(hourly_report["hourly"]["time"], cur_time),
        }
    )

    return daily_report


@app.get("/audio")
async def get_audio(
    message: str = Query(..., title="Message", description="Message"),
    lang: str = Query(..., title="Language", description="Language"),
    tld: str = Query("com", title="TLD", description="TLD"),
):
    root_dir = Path.cwd()
    logger.info(f"Generating audio file in directory: {root_dir}")
    await generate(message, lang, tld)
    file_path = root_dir / "output.mp3"

    async with aiofiles.open(file_path, "rb") as file:
        return StreamingResponse(BytesIO(await file.read()), media_type="audio/mpeg")


# @app.get(path="/process_database")
# async def process_database(response_data):
#     pprint(response_data)
#     token = response_data["access_token"]
#     database_id = response_data["duplicated_template_id"]
#     # database_id = "3a7432d6-f52f-416e-96b1-d1139f109f7f"
#     notion = AsyncClient(auth=token)
#     database = await notion.databases.retrieve(database_id=database_id)
#     pprint(database)

#     pages = await notion.databases.query(database_id=database_id)
#     pprint(pages)
#     return pages


def process_todo_list_page(page):
    return {
        "object_type": page["object"],
        "page_id": page["id"],
        "url": page["url"],
        "title": page["properties"]["Name"]["title"][0]["plain_text"],
        "status": page["properties"]["Status"]["status"]["name"],
        "due_date": page["properties"]["Date"]["date"],
    }


@app.get(path="/get_notion_todo_list")
async def process_notion_todo_list():
    database_id = "19c342cf3da84bd5be5bf00a6559d316"

    pages = await notion.databases.query(database_id=database_id)

    response = [
        process_todo_list_page(page)
        for page in pages["results"]
        if len(page["properties"]["Name"]["title"])
    ]
    sorted_response = sorted(response, key=lambda x: (-ord(x["status"][0]), x["title"]))
    return sorted_response


def process_checklist_page(page):
    return {
        "object_type": page["object"],
        "page_id": page["id"],
        "url": page["url"],
        "title": page["properties"]["Name"]["title"][0]["plain_text"],
        "subject": page["properties"]["Subject"]["multi_select"][0]["name"]
        if page["properties"]["Subject"]["multi_select"]
        else None,
        "checkbox": page["properties"][""]["checkbox"],
    }


@app.get(path="/get_notion_checklist")
async def process_notion_checklist():
    database_id = "3138c97a87704223a6868215a36585a6"

    pages = await notion.databases.query(database_id=database_id)

    response = [
        process_checklist_page(page)
        for page in pages["results"]
        if len(page["properties"]["Name"]["title"])
    ]

    return response


@app.get(path="/notion_checklist_update/{page_id}")
async def notion_checklist_update(page_id: str, checked: bool = Query(...)):
    try:
        await notion.pages.update(
            page_id=page_id,
            properties={"": {"checkbox": checked}},
        )
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update checklist: {str(e)}")


@app.get(path="/notion_checklist_delete/{page_id}")
async def notion_checklist_delete(page_id: str):
    try:
        await notion.pages.update(page_id=page_id, archived=True)
        return Response(status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete checklist: {str(e)}")


class NotionChecklistCreate(BaseModel):
    name: str
    subject: Optional[str] = None


@app.post(path="/notion_checklist_create")
async def notion_checklist_add(NotionChecklistCreate: NotionChecklistCreate):
    try:
        properties = {
            "Name": {
                "title": [{"text": {"content": NotionChecklistCreate.name}}],
            },
        }
        if NotionChecklistCreate.subject:
            properties["Subject"] = {
                "multi_select": [{"name": NotionChecklistCreate.subject}],
            }
        response = await notion.pages.create(
            parent={"database_id": "3138c97a87704223a6868215a36585a6"},
            properties=properties,
        )
        processed_response = process_checklist_page(response)
        return processed_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checklist: {str(e)}")


class NotionTodo(BaseModel):
    name: str


@app.post(path="/notion_todo_create")
async def notion_todo_create(NotionTodo: NotionTodo):
    try:
        properties = {
            "Name": {
                "title": [{"text": {"content": NotionTodo.name}}],
            },
        }
        print(properties)
        properties["Status"] = {
            "status": {"name": "Not started"},
        }
        response = await notion.pages.create(
            parent={"database_id": "19c342cf3da84bd5be5bf00a6559d316"},
            properties=properties,
        )
        processed_response = process_todo_list_page(response)
        return processed_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create todo: {str(e)}")
