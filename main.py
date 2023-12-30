import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()


WORKERS = 2 * os.cpu_count() + 1
PORT = int(os.getenv("PORT"))
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "()": "colorlog.ColoredFormatter",
            "format": ("%(log_color)s%(asctime)s - %(levelname)-8s - %(name)s: %(message)s"),
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        # Define the configuration for the 'uvicorn' logger
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
        },
        # Define the configuration for the 'uvicorn.access' logger
        "uvicorn.access": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


if __name__ == "__main__":
    uvicorn.run(
        "app.server:app", host="0.0.0.0", port=PORT, log_config=LOGGING_CONFIG, workers=WORKERS
    )
