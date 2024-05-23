class BadChoiceError(Exception):
    """Возникает, когда выбор пользователя в дереве команд не поддерживается."""

    def __init__(self, choice: str | None):
        self.message = f"Неподдерживаемый выбор {choice}"
