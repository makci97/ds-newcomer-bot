import typing

from loguru import logger
from telegram import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.error import NetworkError

from utils.constants import MAX_TELEGRM_MESSAGE_LEN


def text_splitter(text: str, max_chunk_size: int = MAX_TELEGRM_MESSAGE_LEN) -> typing.Generator[str, None, None]:
    """Split text to good chunks with size less than max_chunk_size."""
    chunks: list[str] = []
    for chunk in text.split("\n"):
        if len(chunk) <= max_chunk_size:
            chunks.append(f"{chunk}\n")
        else:
            chunks.extend([f"{sentence}." for sentence in chunk.split(".")])
            chunks[-1] = chunks[-1][:-1]

    i: int = 0
    while i < len(chunks):
        cur_text: str = chunks[i]
        j = i + 1
        while j < len(chunks) and len(cur_text + chunks[j]) < max_chunk_size:
            cur_text += chunks[j]
            j += 1
        yield cur_text.strip()
        i = j


async def print_message(
    message: Message,
    text: str,
    parse_mode: ParseMode = ParseMode.MARKDOWN,
    add_finish: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """Print message with errors handling."""
    try:
        await message.reply_text(
            text,
            parse_mode=parse_mode,
            reply_markup=(
                ReplyKeyboardMarkup([[KeyboardButton("/finish_dialog")]], resize_keyboard=True) if add_finish else None
            ),
        )
        await message.reply_text(text, parse_mode=parse_mode)
    except NetworkError:
        logger.error(f"ТГ не смог напечатать текст: \n{text}")
        await message.reply_text("Извините, Телеграм не переварил ответ")
