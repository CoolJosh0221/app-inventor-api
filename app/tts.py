from pydub import AudioSegment
from pathlib import Path
from gtts import gTTS

root_dir = Path.cwd()
file = root_dir / "output.mp3"


async def generate(message: str, lang: str, tld: str):
    """
    Generate speech from the given message and save it as an audio file.

    Args:
        message (str): The message to convert to speech.
        lang (str): The language of the message.
        tld (str): The top-level domain for the gTTS service.
    """
    if message:
        tts = gTTS(message, lang=lang, tld=tld)
        try:
            tts.save(file)
            audio = AudioSegment.from_mp3(file=file)
            silence = AudioSegment.silent(duration=1000)

            combined = audio + silence
            combined.export(file, format="mp3")

        except Exception as e:
            print(f"Error occurred: {e}")
    else:
        print("Message is empty. No speech generated.")
