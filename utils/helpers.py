
from telegram.ext import CallbackContext

"""Helper functions."""

import typing

from loguru import logger
from telegram.ext import CallbackContext

from config.openai_client import client
from utils.constants import ModelName
from utils.prompts import Prompt

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
