"""Constants."""

import typing
from enum import Enum

MAX_TOKENS: typing.Final[int] = 4_096
TEMPERATURE: typing.Final[float] = 0.5


class ModelName(str, Enum):
    """Model names."""

    GPT_4O = "gpt-4o"


class CodePromptMode(str, Enum):
    """Modes for working with code."""

    EXPLAIN = "explain"
    FIND_BUG = "find_bug"
    REFACTOR = "refactor"
    REVIEW = "review"


class TaskPromptMode(str, Enum):
    """Modes for working with tasks."""

    INSTRUCT = "instruct"
    IMPLEMENT = "implement"
