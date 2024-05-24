from io import BytesIO

from openai import OpenAI

from .tokens import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_response(text: str) -> str:
    """Возвращаем текствый ответ."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": text}],
        max_tokens=1024,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()  # type: ignore  # noqa: PGH003


def generate_transcription(audio_bytes: BytesIO) -> str:
    """Возвращаем аудио транскрипт."""
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=("audio.oga", audio_bytes, "audio/ogg"),
    )
    return transcription.text.strip()
