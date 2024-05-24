import base64
from io import BytesIO
from typing import TYPE_CHECKING

from loguru import logger
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config.openai_client import client, generate_transcription
from config.telegram_bot import application
from exceptions.bad_argument_error import BadArgumentError
from exceptions.bad_choice_error import BadChoiceError
from utils.constants import MAX_TOKENS, TEMPERATURE, ModelName
from utils.helpers import check_user_settings, single_text2text_query
from utils.prompts import AlgoTaskMakerPrompt, CodeExplanationPrompt

if TYPE_CHECKING:
    from openai.types.chat.chat_completion import ChatCompletion

# Define states
(
    TASK_CHOICE,
    KNOWLEDGE_GAIN,
    INTERVIEW_PREP,
    PROBLEM_SOL,
    CODE_EXPL,
    CODE_WRITING,
    PROBLEM_HELP,
    EDA,
    MEME_EXPL,
    USER_SETTINGS,
    INTERVIEW_HARD,
    QUESTIONS_HARD,
    INTERN,
    JUNIOR,
    MIDDLE,
    SENIOR,
    EASY,
    MEDIUM,
    HARD,
    ALGO_TASK,
    ML_TASK,
    DIALOG,
) = range(22)

CALLBACK_QUERY_ARG = "update.callback_query"
MESSAGE_ARG = "update.message"
EFFECTIVE_CHAT_ARG = "update.effective_chat"
USER_DATA_ARG = "context.user_data"
I = 0


async def start(update: Update, context: CallbackContext) -> int:
    """Начальный хэндлер дерева команд."""
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    await remove_chat_buttons(update, context)
    context.user_data["dialog"] = []
    keyboard = [
        [InlineKeyboardButton("Прокачка знаний", callback_data="KNOWLEDGE_GAIN")],
        [InlineKeyboardButton("Помоги решить задачу", callback_data="PROBLEM_SOL")],
        [InlineKeyboardButton("Oбъясни IT мем", callback_data="MEME_EXPL")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:  # When /start command is used
        await update.message.reply_text("Выберите задачу:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Выберите задачу:", reply_markup=reply_markup)
    return TASK_CHOICE


async def task_choice(update: Update, _: CallbackContext) -> int:
    """хэндлер выбора базовой группы задач."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data

    if choice == "KNOWLEDGE_GAIN":
        keyboard = [
            [InlineKeyboardButton("Подготовка к собесу", callback_data="INTERVIEW_PREP")],
            [InlineKeyboardButton("Задача по алгоритмам", callback_data="ALGO_TASK")],
            [InlineKeyboardButton("Задача по Ml", callback_data="ML_TASK")],
            [InlineKeyboardButton("Настройки пользователя", callback_data="USER_SETTINGS")],
            [InlineKeyboardButton("Назад", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Ты выбрал прокачку знаний:", reply_markup=reply_markup)
        return KNOWLEDGE_GAIN
    if choice == "PROBLEM_SOL":
        keyboard = [
            [InlineKeyboardButton("Объясни код", callback_data="CODE_EXPL")],
            [InlineKeyboardButton("Напиши код", callback_data="CODE_WRITING")],
            [InlineKeyboardButton("Помоги решить задачу", callback_data="PROBLEM_HELP")],
            [InlineKeyboardButton("EDA датасета", callback_data="EDA")],
            [InlineKeyboardButton("Диалог", callback_data="DIALOG")],
            [InlineKeyboardButton("Назад", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Помощь в решении задачи:", reply_markup=reply_markup)
        return PROBLEM_SOL
    if choice == "MEME_EXPL":
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        keyboard = [
            [InlineKeyboardButton("Отмена", callback_data="CANCEL")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Отправьте мем одним изображением", reply_markup=reply_markup)
        return MEME_EXPL
    raise BadChoiceError(choice)  # type: ignore  # noqa: PGH003


async def knowledge_gain(update: Update, context: CallbackContext) -> int:
    """хэндлер выбора прокачки знаний."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    # if choice == "INTERVIEW_PREP" and check_user_settings(
    #     context,
    # ):
    #     if update.callback_query is None:
    #         raise BadArgumentError(CALLBACK_QUERY_ARG)
    #     await update.callback_query.edit_message_text(
    #         text="Please send a voice message or text reply.",
    #     )
    #     return DIALOG
    if choice == "ALGO_TASK" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        context.user_data["dialog"] = ""
        context.user_data["topic"] = ""
        keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Уровень подготовки: {context.user_data['interview_hard']}\nУровень заданий: {context.user_data['questions_hard']}\nНа какую тему задачу?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),  # type: ignore[arg-type]
        )
        return DIALOG
    # if choice == "ML_TASK" and check_user_settings(context):
    #     if update.callback_query is None:
    #         raise BadArgumentError(CALLBACK_QUERY_ARG)
    #     await update.callback_query.edit_message_text(
    #         text="Please send a voice message or text reply.",
    #     )
    #     return DIALOG
    if choice == "USER_SETTINGS":
        keyboard = [
            [InlineKeyboardButton("Уровень подготовки", callback_data="INTERVIEW_HARD")],
            [InlineKeyboardButton("Сложность заданий", callback_data="QUESTIONS_HARD")],
            [InlineKeyboardButton("BACK", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Настройки:", reply_markup=reply_markup)
        return USER_SETTINGS
    if choice == "BACK":
        return await start(update, context)
    raise BadChoiceError(choice)  # type: ignore  # noqa: PGH003


async def problem_solving(update: Update, context: CallbackContext) -> int:  # noqa: C901, PLR0912
    """хэндлер выбора помощи в решении задач."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "CODE_EXPL":
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        keyboard = [[InlineKeyboardButton("Отмена", callback_data="CANCEL")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Введите код, который нужно объяснить:", reply_markup=reply_markup)
        return CODE_EXPL
    if choice == "CODE_WRITING":
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        await update.callback_query.edit_message_text(text="Скоро мы научимся писать код. Беседа завершена.")
        return ConversationHandler.END
    if choice == "PROBLEM_HELP":
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        await update.callback_query.edit_message_text(
            text="Скоро мы научимся помогать в решении задач. Беседа завершена.",
        )
        return ConversationHandler.END
    if choice == "EDA":
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        await update.callback_query.edit_message_text(text="Скоро мы научимся EDA. Беседа завершена.")
        return ConversationHandler.END
    if choice == "DIALOG":
        if context.user_data is None:
            raise BadArgumentError(USER_DATA_ARG)
        if update.effective_chat is None:
            raise BadArgumentError(EFFECTIVE_CHAT_ARG)
        context.user_data["dialog"] = []
        keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Начинаем диалог",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),  # type: ignore[arg-type]
        )
        return DIALOG
    if choice == "BACK":
        return await start(update, context)
    raise BadChoiceError(choice)  # type: ignore  # noqa: PGH003


async def code_explanation(update: Update, context: CallbackContext) -> int:
    """Хэндлер объяснения кода."""
    query = update.callback_query
    if query and query.data == "CANCEL":
        return await start(update, context)
    if update.message is None or update.message.text is None:
        raise BadArgumentError(MESSAGE_ARG)
    code: str = update.message.text
    prompt: CodeExplanationPrompt = CodeExplanationPrompt(code=code)
    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )
    await update.message.reply_text(text=explanation, parse_mode=ParseMode.MARKDOWN)
    return await start(update, context)


async def user_settings(update: Update, context: CallbackContext) -> int:
    """Хэндлер выбора настроек пользоватея."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "INTERVIEW_HARD":
        keyboard = [
            [InlineKeyboardButton("Intern", callback_data="INTERN")],
            [InlineKeyboardButton("Junior", callback_data="JUNIOR")],
            [InlineKeyboardButton("Middle", callback_data="MIDDLE")],
            [InlineKeyboardButton("Senior", callback_data="SENIOR")],
            [InlineKeyboardButton("BACK", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Настройки:", reply_markup=reply_markup)
        return INTERVIEW_HARD
    if choice == "QUESTIONS_HARD":
        keyboard = [
            [InlineKeyboardButton("easy", callback_data="EASY")],
            [InlineKeyboardButton("medium", callback_data="MEDIUM")],
            [InlineKeyboardButton("hard", callback_data="HARD")],
            [InlineKeyboardButton("BACK", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Настройки:", reply_markup=reply_markup)
        return QUESTIONS_HARD
    if choice == "BACK":
        return await start(update, context)
    raise BadChoiceError(choice)  # type: ignore  # noqa: PGH003


async def interview_hard(update: Update, context: CallbackContext) -> int:
    """Хэндлер выбора уровня знаний."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "INTERN":
        context.user_data["questions_hard"] = choice  # type: ignore  # noqa: PGH003
    if choice == "JUNIOR":
        context.user_data["questions_hard"] = choice  # type: ignore  # noqa: PGH003
    if choice == "MIDDLE":
        context.user_data["questions_hard"] = choice  # type: ignore  # noqa: PGH003
    if choice == "SENIOR":
        context.user_data["questions_hard"] = choice  # type: ignore  # noqa: PGH003
    if choice == "BACK":
        pass
    keyboard = [
        [InlineKeyboardButton("Уровень подготовки", callback_data="INTERVIEW_HARD")],
        [InlineKeyboardButton("Сложность заданий", callback_data="QUESTIONS_HARD")],
        [InlineKeyboardButton("BACK", callback_data="BACK")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Настройки:", reply_markup=reply_markup)
    return USER_SETTINGS


async def questions_hard(update: Update, context: CallbackContext) -> int:
    """Хэндлер выбора сложности вопросов."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "EASY":
        context.user_data["interview_hard"] = choice  # type: ignore  # noqa: PGH003
    if choice == "MEDIUM":
        context.user_data["interview_hard"] = choice  # type: ignore  # noqa: PGH003
    if choice == "HARD":
        context.user_data["interview_hard"] = choice  # type: ignore  # noqa: PGH003
    if choice == "BACK":
        pass
    keyboard = [
        [InlineKeyboardButton("Уровень подготовки", callback_data="INTERVIEW_HARD")],
        [InlineKeyboardButton("Сложность заданий", callback_data="QUESTIONS_HARD")],
        [InlineKeyboardButton("BACK", callback_data="BACK")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Настройки:", reply_markup=reply_markup)
    return USER_SETTINGS


async def meme_explanation(update: Update, context: CallbackContext) -> int:
    """Хэндлер диалога объяснения IT мема."""
    query = update.callback_query
    if query and query.data == "CANCEL":
        return await start(update, context)
    if update.message is None:
        raise BadArgumentError(MESSAGE_ARG)
    await update.message.reply_text(text="Анализируем мем...")
    file = await update.message.photo[-1].get_file()
    data = await file.download_as_bytearray()
    explanation = explain_meme(data)
    await update.message.reply_text(text=f"{explanation}")
    return await start(update, context)


def explain_meme(data: bytearray) -> str:
    """Отправить мем в ChatGPT и получить его строковое описание."""
    bytes_data = bytes(data)
    base64_encoded = base64.b64encode(bytes_data)
    base64_string = base64_encoded.decode("utf-8")
    response: ChatCompletion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        # TODO @ntrubkin: написать промт на объяснение IT мема
                        "text": "Что на изображении?",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_string}",
                        },
                    },
                ],
            },
        ],
        max_tokens=1024,
        temperature=0.5,
    )
    content = response.choices[0].message.content
    if content is None:
        logger.error("OpenAI содержит пустой ответ")
        return ""
    return content.strip()


async def dialog(update: Update, context: CallbackContext) -> int:
    """Хэндлер диалога."""
    if update.message is None:
        raise BadArgumentError(MESSAGE_ARG)
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    if update.message.voice:

        audio_file = await context.bot.get_file(update.message.voice.file_id)

        audio_bytes = BytesIO(await audio_file.download_as_bytearray())

        text: str = generate_transcription(audio_bytes)

    if update.message.text:
        text = update.message.text

    if context.user_data["topic"] == "":
        context.user_data["topic"] = text
    else:
        context.user_data["dialog"] += text

    prompt: AlgoTaskMakerPrompt = AlgoTaskMakerPrompt(
        questions_hard=context.user_data["questions_hard"],
        interview_hard=context.user_data["interview_hard"],
        topic=context.user_data["topic"],
        code=context.user_data["dialog"],
    )
    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    await update.message.reply_text(text=explanation, parse_mode=ParseMode.MARKDOWN)
    return DIALOG


async def finish_dialog(update: Update, context: CallbackContext) -> int:
    """Завершает диалог."""
    if update.message is None:
        raise BadArgumentError(MESSAGE_ARG)
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    await update.message.reply_text(
        text="Рад был помочь",
        reply_markup=ReplyKeyboardRemove(),
    )
    """Хэндлер завершения диалога"""
    return await start(update, context)


async def remove_chat_buttons(
    update: Update,
    context: CallbackContext,
    msg_text: str = r"_It is not the message you are looking for\.\.\._",
) -> None:
    """Delete buttons below the chat.

    For now there are no way to delete kbd other than inline one, check
        https://core.telegram.org/bots/api#updating-messages.
    """
    if update.effective_chat is None:
        raise BadArgumentError(EFFECTIVE_CHAT_ARG)
    msg = await context.bot.send_message(update.effective_chat.id, msg_text, reply_markup=ReplyKeyboardRemove())
    await msg.delete()


async def cancel(update: Update, _: CallbackContext) -> int:
    """Завершает беседу."""
    if update.message is None:
        raise BadArgumentError(MESSAGE_ARG)
    await update.message.reply_text("Беседа завершена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


"""Run the bot."""
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        TASK_CHOICE: [CallbackQueryHandler(task_choice)],
        KNOWLEDGE_GAIN: [CallbackQueryHandler(knowledge_gain)],
        PROBLEM_SOL: [CallbackQueryHandler(problem_solving)],
        USER_SETTINGS: [CallbackQueryHandler(user_settings)],
        INTERVIEW_HARD: [CallbackQueryHandler(interview_hard)],
        QUESTIONS_HARD: [CallbackQueryHandler(questions_hard)],
        CODE_EXPL: [CallbackQueryHandler(code_explanation), MessageHandler(filters.TEXT, code_explanation)],
        MEME_EXPL: [CallbackQueryHandler(meme_explanation), MessageHandler(filters.PHOTO, meme_explanation)],
        DIALOG: [
            MessageHandler(~filters.COMMAND, dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler("start", start))

# Запуск бота
application.run_polling()
