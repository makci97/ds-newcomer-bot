from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from config.openai_client import client


async def chatgpt_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
    """Начало взаимодействия с пользователем, если он пишет в чат."""
    # текст входящего сообщения
    text = update.message.text

    # запрос
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": text}],
        max_tokens=1024,
        temperature=0.5,
    )

    # ответ
    reply = response.choices[0].message.content.strip()

    # перенаправление ответа в Telegram
    await update.message.reply_text(reply)

    logger.debug("user:", text)
    logger.debug("assistant:", reply)
