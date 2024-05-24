from telegram.ext import CallbackContext


def check_user_settings(context: CallbackContext) -> bool:
    """проверка если настройки пользвателя заданы."""
    return context.user_data["interview_hard"] and context.user_data["questions_hard"]  # type: ignore  # noqa: PGH003
