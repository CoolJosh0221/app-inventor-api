import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()


def main():
    uvicorn.run(
        app="app.server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT")),
        proxy_headers=True,
        workers=4,
    )


if __name__ == "__main__":
    main()
