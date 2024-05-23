import json

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes


async def start_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
    """Начало взаимодействия с пользователем, если он отправляет команду в чат."""
    # объект обновления
    update_obj = json.dumps(update.to_dict(), indent=4)

    # ответ
    reply = "*update object*\n\n" + "```json\n" + update_obj + "\n```"

    if update.message is None:
        logger.error("Message not found")
        return

    # перенаправление ответа в Telegram
    await update.message.reply_text(reply, parse_mode="Markdown")

    logger.debug("assistant:", reply)
