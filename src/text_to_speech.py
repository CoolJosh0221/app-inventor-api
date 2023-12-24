import os
from gtts import gTTS


async def generate(message: str, lang: str, tld: str):
    """
    Generate speech from the given message and save it as an audio file.

    Args:
        message (str): The message to convert to speech.
        lang (str): The language of the message.
        tld (str): The top-level domain for the gTTS service.
    """
    if message:
        root_dir = os.getcwd()

        tts = gTTS(message, lang=lang, tld=tld)
        try:
            tts.save(f"{root_dir}/audio/output.mp3")
        except Exception as e:
            print(f"Error occurred during tts.save: {e}")
    else:
        print("Message is empty. No speech generated.")
