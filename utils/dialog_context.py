from typing import Any


class DialogContext:
    """Модель диалога с ChatGPT."""

    def __init__(self, model: str, max_tokens: int, temperature: float):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.messages: Any = []
