import inspect
import os
from gtts import gTTS


async def generate(message: str, lang: str, tld: str):
    root_dir = os.getcwd()

    tts = gTTS(message, lang=lang, tld=tld)
    tts.save(f"{root_dir}/audio/output.mp3")
