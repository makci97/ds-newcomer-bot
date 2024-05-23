from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, CommandHandler, filters, ConversationHandler, ContextTypes, \
    CallbackQueryHandler
from config.telegram_bot import application
from handlers.message_handlers import chatgpt_reply
from handlers.command_handlers import start_reply

# Define states
TASK_CHOICE, KNOWLEDGE_GAIN, INTERVIEW_PREP, PROBLEM_SOL, CODE_EXPL, CODE_WRITING, PROBLEM_HELP, EDA, MEME_EXPL = range(9)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton('Прокачка знаний', callback_data='KNOWLEDGE_GAIN')],
        [InlineKeyboardButton('Помоги решить задачу', callback_data='PROBLEM_SOL')],
        [InlineKeyboardButton('Oбъясни IT мем', callback_data='MEME_EXPL')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:  # When /start command is used
        await update.message.reply_text('Выберите задачу:', reply_markup=reply_markup)
    else:  # When restarting from the end of the conversation
        await update.callback_query.edit_message_text('Please choose:', reply_markup=reply_markup)
    return TASK_CHOICE


async def task_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'KNOWLEDGE_GAIN':
        keyboard = [
            [InlineKeyboardButton("Подготовка к собесу", callback_data='INTERVIEW_PREP')],
            [InlineKeyboardButton("Назад", callback_data='BACK')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Ты выбрал прокачку знаний:", reply_markup=reply_markup)
        return KNOWLEDGE_GAIN
    elif choice == 'PROBLEM_SOL':
        keyboard = [
            [InlineKeyboardButton("Объясни код", callback_data='CODE_EXPL')],
            [InlineKeyboardButton("Напиши код", callback_data='CODE_WRITING')],
            [InlineKeyboardButton("Помоги решить задачу", callback_data='PROBLEM_HELP')],
            [InlineKeyboardButton("EDA датасета", callback_data='EDA')],
            [InlineKeyboardButton("Назад", callback_data='BACK')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Помощь в решении задачи:", reply_markup=reply_markup)
        return PROBLEM_SOL
    elif choice == 'MEME_EXPL':
        await update.callback_query.edit_message_text(text="Скоро мы научимся объяснять мемы. Беседа завершена")
        return ConversationHandler.END


async def knowledge_gain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == 'INTERVIEW_PREP':
        await query.edit_message_text(text="Подготовка к собесу скоро будет доступна. Беседа завершена")
        return ConversationHandler.END
    elif choice == 'BACK':
        return await start(update, context)


async def problem_solving(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == 'CODE_EXPL':
        await update.callback_query.edit_message_text(text="Скоро мы научимся объяснять код. Беседа завершена")
        return ConversationHandler.END
    elif choice == 'CODE_WRITING':
        await update.callback_query.edit_message_text(text="Скоро мы научимся писать код. Беседа завершена")
        return ConversationHandler.END
    elif choice == 'PROBLEM_HELP':
        await update.callback_query.edit_message_text(text="Скоро мы научимся помогать в решении задач. Беседа завершена")
        return ConversationHandler.END
    elif choice == 'EDA':
        await update.callback_query.edit_message_text(text="Скоро мы научимся EDA. Беседа завершена")
        return ConversationHandler.END
    elif choice == 'BACK':
        return await start(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text('Bye! Hope to talk to you again soon.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


"""Run the bot."""


class Filters:
    pass


conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        TASK_CHOICE: [CallbackQueryHandler(task_choice)],
        KNOWLEDGE_GAIN: [CallbackQueryHandler(knowledge_gain)],
        PROBLEM_SOL: [CallbackQueryHandler(problem_solving)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler('start', start))

# Запуск бота
application.run_polling()
