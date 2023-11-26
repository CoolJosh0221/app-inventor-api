import uuid
import random
import string
from gtts import gTTS


async def generate(message: str, lang: str):
    tts = gTTS(message, lang=lang)
    tts.save("audio/output.mp3")
