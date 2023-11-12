import os
from pprint import pprint
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

print(os.environ["NOTION_TOKEN"])

notion = Client(auth=os.environ["NOTION_TOKEN"])


def list_users():
    list_users_response = notion.users.list()
    pprint(list_users_response)


if __name__ == '__main__':
    list_users()
