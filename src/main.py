import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run("server:app", port=os.getenv("PORT"), log_level="info")
