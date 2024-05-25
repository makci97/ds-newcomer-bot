"""Prompt builders."""

import base64
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
    def messages(self) -> typing.Iterable[ChatCompletionMessageParam]:
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
                Разбери решение пользователя когда он тебе ответит
        """
        return [{"role": "system", "content": prompt}, *self.reply]


@dataclass
class MLTaskMakerPrompt(Prompt):
    """Prompt builder for ml task scenario."""

    questions_hard: str
    interview_hard: str
    topic: str
    reply: dict

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt for ml scenario."""
        prompt: str = f"""
                Представь, что ты опытный IT-рекрутер, проводящий техническое собеседование
                с кандидатом на позицию {self.interview_hard} DS-разработчика.
                Сформулируй задачу на алгоритмы (описание условий, пример данных на вход и выход)
                и задай по ней вопросы(память и время выполнение) на тему {self.topic} уровня {self.questions_hard}
                без подсказок и не показывай правильный ответ пока пользователь не отправит свое решение.
                Разбери решение пользователя когда он тебе ответит
        """
        return [{"role": "system", "content": prompt}, *self.reply]


@dataclass
class InterviewMakerPrompt(Prompt):
    """Prompt builder for interview task scenario."""

    questions_hard: str
    interview_hard: str
    topic: str
    reply: dict

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt for interview scenario."""
        prompt: str = f"""
                Представь, что ты опытный IT-рекрутер, проводящий техническое собеседование
                с кандидатом на позицию {self.interview_hard} DS-разработчика. Вопросы должны быть по теме: {self.topic}
                Сформулируй две задачи на алгоритмы(описание условий, пример данных на вход и выход)
                уровня {self.questions_hard} и серию вопросов по уровня {self.questions_hard}
                без подсказок и не показывай правильныйответ пока пользователь не отправит свое решение
                Разбери решение пользователя когда он тебе ответит
        """
        return [{"role": "system", "content": prompt}, *self.reply]


@dataclass
class TestMakerPrompt(Prompt):
    """Prompt builder for interview task scenario."""

    questions_hard: str
    interview_hard: str
    topic: str
    reply: dict

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt for interview scenario."""
        prompt: str = f"""
                Выступая в роли опытного IT-рекрутера, вы столкнулись с задачей помочь {self.interview_hard}
                DS-разработчику в подготовке к теме {self.topic} различного уровня сложности:
                {self.questions_hard}.Вам необходимо предоставить тест с вариантами ответов,
                который поможет им оценить свои знания и умения.
                Важно, чтобы тест был разнообразным и не требовал подсказок.
                Правильные ответы не следует показывать до тех пор, пока пользователь не отправит свое решение.
                Разбери решение пользователя когда он тебе ответит
        """
        return [{"role": "system", "content": prompt}, *self.reply]


@dataclass
class RoadMapMakerPrompt(Prompt):
    """Prompt builder for interview task scenario."""

    questions_hard: str
    interview_hard: str
    topic: str
    reply: dict

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt for interview scenario."""
        prompt: str = f"""
                    Выступая в роли опытного IT-рекрутера, вы столкнулись с задачей помочь
                    {self.interview_hard} DS-разработчику в подготовке к теме {self.topic} уровня сложности:
                    {self.questions_hard}. Вам необходимо предоставить план с пунктами, которые
                    помогут им освоить эту тему. Важно, чтобы пункты были разнообразными и не требовали ссылок.
        """
        return [{"role": "system", "content": prompt}, *self.reply]


@dataclass
class PsychoHelpPrompt(Prompt):
    """Prompt builder for interview task scenario."""

    reply: dict

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Message history with a prompt for interview scenario."""
        prompt: str = """
                Представь, что ты опытный психолог, и к тебе пришел DS-разработчик.
                И просит помочь ему подготовиться к собеседованию.
                Ответь на его вопросы и помоги ему
        """
        return [{"role": "system", "content": prompt}, *self.reply]


@dataclass
class MemeImagePrompt(Prompt):
    """Prompt builder for meme explanation scenario."""

    image: bytearray

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Meme scenario prompt."""
        prompt: str = """Представь, что ты столкнулся с мемом, который вызывает у тебя смех. Важно не описать
         картинку, а понять, почему этот мем смешной. Ответь коротко на следующие вопросы: Какие элементы мема
         вызывают смех? Какая основная идея или шутка заложена в меме? Есть ли какие-либо культурные или
         интернет-отсылки, которые следует знать, чтобы понять мем? Ответ не структурируй."""
        bytes_data = bytes(self.image)
        base64_encoded = base64.b64encode(bytes_data)
        base64_string = base64_encoded.decode("utf-8")
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_string}",
                        },
                    },
                ],
            },
        ]


@dataclass
class MemeNeedReactionPrompt(Prompt):
    """Prompt builder for meme reaction scenario."""

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """Meme reaction prompt."""
        prompt: str = """Представьте, что вам прислали в чат мем. Вам нужно отреагировать на него в чате так, чтобы
         показать, что вы его поняли."""
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            },
        ]


@dataclass
class GenericUserTextPrompt(Prompt):
    """Prompt builder for text user message."""

    text: str

    @property
    def messages(self: typing.Self) -> typing.Iterable[ChatCompletionMessageParam]:
        """User text prompt."""
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": self.text,
                    },
                ],
            },
        ]
