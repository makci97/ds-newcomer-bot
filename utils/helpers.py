"""Helper functions."""

import typing

from loguru import logger
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads import TextContentBlock
from telegram.error import NetworkError
from telegram.ext import CallbackContext

from config.openai_client import client
from utils.constants import ModelName
from utils.prompts import Prompt
from utils.utils import text_splitter

if typing.TYPE_CHECKING:
    from openai.types.chat.chat_completion import ChatCompletion


def single_text2text_query(model: ModelName, prompt: Prompt, max_tokens: int, temperature: float) -> str:
    """Make a query to an LLM model and return its reply."""
    response: ChatCompletion = client.chat.completions.create(
        model=model,
        messages=prompt.messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    if reply := response.choices[0].message.content:
        return reply.strip()

    msg: str = "Empty OpenAI response context"
    logger.error(msg)
    raise ValueError(msg)


def check_user_settings(context: CallbackContext) -> bool:
    """проверка если настройки пользвателя заданы."""
    return context.user_data["interview_hard"] and context.user_data["questions_hard"]  # type: ignore  # noqa: PGH003


def gen_messages_from_eda_stream(thread: Thread, eda_assistant: Assistant) -> typing.Generator[str, None, None]:
    """Get messages from stream for dataset processing."""
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=eda_assistant.id,
    ) as stream:
        for event in stream:
            if event.event == "thread.message.completed":
                for content in event.data.content:
                    if isinstance(content, TextContentBlock):
                        text: str = content.text.value
                        logger.debug(f"{text=}")
                        text = text.replace("\\n", "\n")
                        logger.debug(f"{text=}")
                        for chunk in text_splitter(text=text):
                            try:
                                yield chunk
                            except NetworkError:
                                yield "Извините, ответ не может быть выведен в сообщении в Телеграм."
