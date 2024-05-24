import base64
from typing import Any


class DialogContext:
    """Модель диалога с ChatGPT."""

    def __init__(self, model: str, max_tokens: int, temperature: float):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.messages: Any = []

    def append_user_text(self, text: str) -> None:
        """Добавить новое сообщение от юзера с определенным текстом."""
        self.messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                    },
                ],
            },
        )

    def append_user_image(self, image: bytearray, text: str) -> None:
        """Добавить новое сообщение от юзера с картинкой и поясняющим текстом."""
        bytes_data = bytes(image)
        base64_encoded = base64.b64encode(bytes_data)
        base64_string = base64_encoded.decode("utf-8")
        self.messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_string}",
                        },
                    },
                ],
            },
        )
