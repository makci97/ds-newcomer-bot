"""Prompt builders."""

import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass

from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from utils.constants import CodePromptMode, TaskPromptMode


@dataclass
class Prompt(ABC):
    """Prompt builder."""

    @property
    @abstractmethod
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Final message history to be sent to LLM."""
        raise NotImplementedError


@dataclass
class CodePrompt(Prompt):
    """Prompt builder for code explanation scenario."""

    code: str
    mode: CodePromptMode

    @property
    def _instruction(self: typing.Self) -> str:
        if self.mode == CodePromptMode.EXPLAIN:
            return """You should analyse, explain and interpret it.

            Your response should consist of two parts:
            1. Textual description of what the code does in general.
            2. The very same code with inline comments where you explain everything step by step.
            """

        if self.mode == CodePromptMode.FIND_BUG:
            return """Analyse it.

            Your response instructions:
            1. If there are no bugs, confirm to the user that you have not found any potential problems in the code.
            2. If there are some issues, highlight what they are and how to fix them. In this case, you should:
                - Provide textual description of all bugs and problems that you have found
                - Provide the fixed version of the code with inline comments about what you have changed
            """

        if self.mode == CodePromptMode.REFACTOR:
            return """Refactor it to improve readability, efficiency, and maintainability.
            Identify areas where the code can be simplified, optimized, and made more efficient.
            Consider breaking down complex functions into smaller, more modular ones,
            eliminating redundant code, and adhering to best practices and coding conventions.
            You may as well split the code into several separate modules if needed.

            In your response, be sure to provide the user with:
            1. Detailed description of the proposed changes.
            2. Refactored version of the code.
            """

        if self.mode == CodePromptMode.REVIEW:
            return """Review the code and provide detailed feedback on the following aspects:
            - Syntax and logic errors
            - Performance bottlenecks
            - Security vulnerabilities
            - Coding standard and naming consistencies
            - Adherence to best practices
            - Overall design and architecture
            - Scalability
            - Time and memory complexity
            - Readability and maintainability
            - Platform-specific issues
            - Presence of unit tests

            This list is not exhaustive. Provide a thorough analysis and any recommendations for improvements.
            """

        msg: str = f"Unknown mode: {self.mode}"
        raise NotImplementedError(msg)

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt to retrieve code explanation."""
        prompt: str = (
            f"You are a virtual assistant for a data scientist. They will send you some code. {self._instruction}"
        )

        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": self.code},
        ]


@dataclass
class TaskPrompt(Prompt):
    """Prompt builder for code explanation scenario."""

    task: str
    mode: TaskPromptMode

    @property
    def _instruction(self: typing.Self) -> str:
        if self.mode == TaskPromptMode.INSTRUCT:
            return """Based on the task description, generate a set of clear, concise, and actionable instructions
            that will guide someone through the completion of the task. The instructions should be easy to follow
            and should cover all necessary steps, tools, and considerations to ensure successful completion.

            Ensure the following:
            1. Break down the task into sequential steps.
            2. Use simple and precise language.
            3. Include any prerequisites or preparation needed before starting the task.
            4. Mention any specific tools, materials, libraries, or resources required.
            5. Highlight any important tips or warnings.
            6. Ensure the instructions are logically ordered and easy to understand.
            """

        if self.mode == TaskPromptMode.IMPLEMENT:
            return """Your should write code based on this description.

            Ensure the following:
            1. Your code is clean, well-documented, and adheres to best practices
            2. You use the appropriate programming language as inferred from the task description.
                If the language is explicitly mentioned, use that language.
            3. Your code is modular, with functions/classes as needed.
            4. There are comments within the code to explain key sections and logic.
                If applicable, provide a brief documentation or usage guide.
            5. Your code handles errors to manage potential exceptions or edge cases.
            6. Your code is optimized for performance where applicable.
            7. You have included a set of test cases or a simple testing framework to validate the functionality.
            """

        msg: str = f"Unknown mode: {self.mode}"
        raise NotImplementedError(msg)

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt to retrieve code explanation."""
        prompt: str = f"""You are a virtual assistant for a data scientist.
        In their message, they will send you a description of their task.
        {self._instruction}
        """

        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": self.task},
        ]


@dataclass
class AlgoTaskMakerPrompt(Prompt):
    """Prompt builder for algo task scenario."""

    questions_hard: str
    interview_hard: str
    topic: str
    reply: dict

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt for algo scenario."""
        prompt: str = f"""
                Представь, что ты опытный IT-рекрутер, проводящий техническое собеседование
                с кандидатом на позицию {self.interview_hard} DS-разработчика.
                Сформулируй задачу на алгоритмы (описание условий, пример данных на вход и выход)
                и задай по ней вопросы(память и время выполнение) на тему {self.topic} уровня {self.questions_hard}
                без подсказок и не показывай правильный ответ пока пользователь не отправит свое решение.
                Когда пользователь пришлет решение разбери его и если решение не правильное приведи правильное
        """
        return [{"role": "system", "content": prompt}, *self.reply]
