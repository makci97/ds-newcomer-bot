"""Prompt builders."""

import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass

from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam


@dataclass
class Prompt(ABC):
    """Prompt builder."""

    @property
    @abstractmethod
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Final message history to be sent to LLM."""
        raise NotImplementedError


@dataclass
class CodeExplanationPrompt(Prompt):
    """Prompt builder for code explanation scenario."""

    code: str

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt to retrieve code explanation."""
        prompt: str = """
            You are a virtual assistant for a data scientist.
            They will send you some code, which you should analyse, explain and interpret.

            Your response should consist of two parts:
            1. Textual description of what the code does in general.
            2. The very same code with inline comments where you explain everything step by step.
        """

        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": self.code},
        ]
