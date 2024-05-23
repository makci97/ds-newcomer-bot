from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler

from config.telegram_bot import application
from exceptions.bad_argument_error import BadArgumentError
from exceptions.bad_choice_error import BadChoiceError

# Define states
TASK_CHOICE, KNOWLEDGE_GAIN, INTERVIEW_PREP, PROBLEM_SOL, CODE_EXPL, CODE_WRITING, PROBLEM_HELP, EDA, MEME_EXPL, USER_SETTINGS, INTERVIEW_HARD, QUESTIONS_HARD,INTERN, JUNIOR, MIDDLE, SENIOR, EASY, MEDIUM, HARD = range(
    19,
)

CALLBACK_QUERY_ARG = "update.callback_query"
MESSAGE_ARG = "update.message"


async def start(update: Update, _: CallbackContext) -> int:
    """Начальный хэндлер дерева команд."""
    keyboard = [
        [InlineKeyboardButton("Прокачка знаний", callback_data="KNOWLEDGE_GAIN")],
        [InlineKeyboardButton("Помоги решить задачу", callback_data="PROBLEM_SOL")],
        [InlineKeyboardButton("Oбъясни IT мем", callback_data="MEME_EXPL")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:  # When /start command is used
        await update.message.reply_text("Выберите задачу:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Please choose:", reply_markup=reply_markup)
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
            [InlineKeyboardButton("Назад", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Помощь в решении задачи:", reply_markup=reply_markup)
        return PROBLEM_SOL
    if choice == "MEME_EXPL":
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        await update.callback_query.edit_message_text(text="Скоро мы научимся объяснять мемы. Беседа завершена.")
        return ConversationHandler.END
    raise BadChoiceError(choice)


async def knowledge_gain(update: Update, context: CallbackContext) -> int:
    """хэндлер выбора прокачки знаний."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "INTERVIEW_PREP":
        await query.edit_message_text(text=f"Уровень подготовки: {context.user_data['interview_hard']} Уровень сложности: {context.user_data['questions_hard']}")
        return ConversationHandler.END
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
    raise BadChoiceError(choice)


async def problem_solving(update: Update, context: CallbackContext) -> int:
    """хэндлер выбора помощи в решении задач."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "CODE_EXPL":
        await code_explanation(update, context)
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
    if choice == "BACK":
        return await start(update, context)
    raise BadChoiceError(choice)


async def code_explanation(update: Update, _: CallbackContext) -> int:
    """Хэндлер выбора объяснения кода."""
    if update.callback_query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await update.callback_query.edit_message_text(text="Скоро мы научимся объяснять код. Беседа завершена.")
    return ConversationHandler.END


async def user_settings(update, context):
    """Настройки сложности вопросов."""
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
    raise BadChoiceError(choice)

async def interview_hard(update, context):
    """Настройки уровня знаний."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "INTERN":
        context.user_data["questions_hard"] = choice
        await query.edit_message_text(text="Выбран уровень подгтовоки.")
        return await user_settings(update, context)
    if choice == "JUNIOR":
        context.user_data["questions_hard"] = choice
        await query.edit_message_text(text="Выбран уровень подгтовоки.")
        return await user_settings(update, context)
    if choice == "MIDDLE":
        context.user_data["questions_hard"] = choice
        await query.edit_message_text(text="Выбран уровень подгтовоки.")
        return await start(update, context)
    if choice == "SENIOR":
        context.user_data["questions_hard"] = choice
        await query.edit_message_text(text="Выбран уровень подгтовоки.")
        return await start(update, context)
    if choice == "BACK":
        return await start(update, context)
    raise BadChoiceError(choice)

async def questions_hard(update, context):
    """Настройки уровня сложности вопросов."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "EASY":
        context.user_data["interview_hard"] = choice
        await query.edit_message_text(text="Выбран уровень сложности.")
        return await start(update, context)
    if choice == "MEDIUM":
        context.user_data["interview_hard"] = choice
        await query.edit_message_text(text="Выбран уровень сложности.")
        return await start(update, context)
    if choice == "HARD":
        context.user_data["interview_hard"] = choice
        await query.edit_message_text(text="Выбран уровень сложности.")
        return await start(update, context)
    if choice == "BACK":
        return await start(update, context)
    raise BadChoiceError(choice)


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
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler("start", start))

# Запуск бота
application.run_polling()
