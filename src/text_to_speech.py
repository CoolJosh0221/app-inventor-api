import uuid
import random
import string
from gtts import gTTS


async def generate(message: str, lang: str) -> str:
    file_id = str(uuid.uuid4())

    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    file_name = f"{file_id}_{random_string}.mp3"

    tts = gTTS(message, lang=lang)
    tts.save(f"audio/{file_name}")

    return file_name
