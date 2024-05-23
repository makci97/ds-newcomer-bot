class BadArgumentError(Exception):
    """Возникает, когда в метод прилетает некорректный аргумент."""

    def __init__(self, arg_name: str):
        self.message = f"Некорректный аргумент{arg_name}"
