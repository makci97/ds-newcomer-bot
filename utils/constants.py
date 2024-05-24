"""Constants."""

import typing
from enum import Enum

MAX_TOKENS: typing.Final[int] = 4_096
MAX_TELEGRM_MESSAGE_LEN: int = 4000
TEMPERATURE: typing.Final[float] = 0.5


class ModelName(str, Enum):
    """Model names."""

    GPT_4O = "gpt-4o"
