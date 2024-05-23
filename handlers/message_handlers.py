from typing import TYPE_CHECKING

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from config.openai_client import client

if TYPE_CHECKING:
    from openai.types.chat.chat_completion import ChatCompletion


async def chatgpt_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
    """Начало взаимодействия с пользователем, если он пишет в чат."""
    if update.message is None:
        logger.error("Message not found")
        return

    if update.message.text is None:
        logger.error("Text is empty")
        return

    # текст входящего сообщения
    text: str = update.message.text

    # запрос
    response: ChatCompletion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": text}],
        max_tokens=1024,
        temperature=0.5,
    )

    reply: str
    if response.choices[0].message.content is None:
        reply = "OpenAI response context is empty"
        logger.error(reply)
    else:
        # ответ
        reply = response.choices[0].message.content.strip()

    # перенаправление ответа в Telegram
    await update.message.reply_text(reply)

    logger.debug("user:", text)
    logger.debug("assistant:", reply)
