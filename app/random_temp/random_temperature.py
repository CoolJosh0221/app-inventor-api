import os.path
import random
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "1w1TKfZgLBxAK-DlxJW4nmZ3AOZbaeilZZuJLJ2hfdzM"
SAMPLE_RANGE_NAME = "Sheet1!A1"


import asyncio


async def main():
    creds = None
    if os.path.exists("app/random_temp/token.json"):
        creds = Credentials.from_authorized_user_file("app/random_temp/token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "app/random_temp/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("app/random_temp/token.json", "w") as token:
            token.write(creds.to_json())

    while True:
        try:
            service = build("sheets", version="v4", credentials=creds)
            values = [
                [
                    random.randint(27, 31),
                ],
            ]
            body = {"values": values}
            result = (
                await service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=SAMPLE_SPREADSHEET_ID,
                    range=SAMPLE_RANGE_NAME,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
            )
            print(f"{result.get('updatedCells')} cells updated.")

        except KeyboardInterrupt:
            exit()

        except HttpError as err:
            print(err)

        await asyncio.sleep(10)


if __name__ == "__main__":
    main()
