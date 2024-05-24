import base64
import io
from io import BytesIO
from typing import TYPE_CHECKING

from loguru import logger
from telegram import (
    Document,
    File,
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

from config.openai_client import client, generate_response, generate_transcription
from config.telegram_bot import application
from exceptions.bad_argument_error import BadArgumentError
from exceptions.bad_choice_error import BadChoiceError
from utils.constants import MAX_TOKENS, TEMPERATURE, CodePromptMode, ModelName, TaskPromptMode
from utils.dialog_context import DialogContext
from utils.helpers import check_user_settings, gen_messages_from_eda_stream, single_text2text_query
from utils.prompts import CodePrompt, Prompt, TaskPrompt

if TYPE_CHECKING:
    from openai.types.beta.assistant import Assistant
    from openai.types.beta.thread import Thread
    from openai.types.chat.chat_completion import ChatCompletion
    from openai.types.file_object import FileObject

# Define states
(
    TASK_CHOICE,
    KNOWLEDGE_GAIN,
    INTERVIEW_PREP,
    PROBLEM_SOL,
    CODE_HELP,
    TASK_HELP,
    HELP_FACTORY,
    EDA,
    MEME_EXPL,
    MEME_EXPL_DIALOG,
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
    USER_REPLY,
    DIALOG,
) = range(24)

CALLBACK_QUERY_ARG = "update.callback_query"
MESSAGE_ARG = "update.message"
EFFECTIVE_CHAT_ARG = "update.effective_chat"
USER_DATA_ARG = "context.user_data"


async def start(update: Update, context: CallbackContext) -> int:
    """Начальный хэндлер дерева команд."""
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    await remove_chat_buttons(update, context)
    context.user_data["dialog"] = None
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
            [InlineKeyboardButton("Скину описание задачи", callback_data="TASK_HELP")],
            [InlineKeyboardButton("Скину код", callback_data="CODE_HELP")],
            [InlineKeyboardButton("Скину датасет", callback_data="EDA")],
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
    if choice == "INTERVIEW_PREP" and check_user_settings(
        context,
    ):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        await update.callback_query.edit_message_text(
            text="Please send a voice message or text reply.",
        )
        return USER_REPLY
    if choice == "ALGO_TASK" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        await update.callback_query.edit_message_text(
            text="Please send a voice message or text reply.",
        )
        return USER_REPLY
    if choice == "ML_TASK" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        await update.callback_query.edit_message_text(
            text="Please send a voice message or text reply.",
        )
        return USER_REPLY
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


async def problem_solving(update: Update, context: CallbackContext) -> int:  # noqa: C901
    """хэндлер выбора помощи в решении задач."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data

    if choice == "CODE_HELP":
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        keyboard = [
            [InlineKeyboardButton("Объяснить", callback_data=CodePromptMode.EXPLAIN)],
            [InlineKeyboardButton("Пофиксить", callback_data=CodePromptMode.FIND_BUG)],
            [InlineKeyboardButton("Отрефакторить", callback_data=CodePromptMode.REFACTOR)],
            [InlineKeyboardButton("Поревьюить", callback_data=CodePromptMode.REVIEW)],
            [InlineKeyboardButton("BACK", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Что нужно сделать с кодом?", reply_markup=reply_markup)
        return CODE_HELP

    if choice == "TASK_HELP":
        keyboard = [
            [InlineKeyboardButton("Подготовить детальное описание", callback_data=TaskPromptMode.INSTRUCT)],
            [InlineKeyboardButton("Написать готовый код", callback_data=TaskPromptMode.IMPLEMENT)],
            [InlineKeyboardButton("BACK", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Что нужно сделать на основе описания?", reply_markup=reply_markup)
        return TASK_HELP

    if choice == "EDA":
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        keyboard = [[InlineKeyboardButton("Отмена", callback_data="CANCEL")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="""Отправьте датасет в csv-формате.
Если у вас пока нет датасета, можете скачать интересные не заезженные датасеты:
https://www.kaggle.com/datasets?topic=trendingDataset """,
            reply_markup=reply_markup,
        )
        return EDA
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
        context.user_data["dialog"] = DialogContext(
            model=ModelName.GPT_4O,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        return DIALOG
    if choice == "BACK":
        return await start(update, context)
    raise BadChoiceError(choice)  # type: ignore  # noqa: PGH003


async def code_help(update: Update, context: CallbackContext) -> int:
    """Хэндлер помощи по коду."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "BACK":
        return await start(update, context)

    context.user_data["prompt_type"] = "code_help"  # type: ignore[index]
    context.user_data["prompt_mode"] = choice  # type: ignore[index]

    await query.edit_message_text(text="Ваш код:")
    return HELP_FACTORY


async def task_help(update: Update, context: CallbackContext) -> int:
    """Хэндлер помощи по описанию задачи."""
    query = update.callback_query
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "BACK":
        return await start(update, context)

    context.user_data["prompt_type"] = "task_help"  # type: ignore[index]
    context.user_data["prompt_mode"] = query.data  # type: ignore[index]

    await query.edit_message_text(text="Описание вашей задачи:")
    return HELP_FACTORY


async def help_factory(update: Update, context: CallbackContext) -> int:
    """Хэндлер запроса-ответа для помощи по коду/заданию."""
    if update.message is None or (user_input := update.message.text) is None:
        raise BadArgumentError(MESSAGE_ARG)

    if context.user_data["prompt_type"] == "code_help":  # type: ignore[index]
        prompt: Prompt = CodePrompt(
            code=user_input,
            mode=context.user_data["prompt_mode"],  # type: ignore[index]
        )  # type: ignore[call-overload]

    if context.user_data["prompt_type"] == "task_help":  # type: ignore[index]
        prompt = TaskPrompt(
            task=user_input,
            mode=context.user_data["prompt_mode"],  # type: ignore[index]
        )  # type: ignore[call-overload]

    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    await update.message.reply_text(text=explanation, parse_mode=ParseMode.MARKDOWN)
    return await start(update, context)


async def eda(update: Update, context: CallbackContext) -> int:
    """Хэндлер исследовательского анализа датасета."""
    query = update.callback_query
    if query and query.data == "CANCEL":
        return await start(update, context)
    if update.message is None or update.message.document is None:
        raise BadArgumentError(MESSAGE_ARG)

    logger.info("Download dataset from chat")
    stream_dataset: io.BytesIO = io.BytesIO()
    file: File = await context.bot.get_file(update.message.document)
    await file.download_to_memory(stream_dataset)

    logger.info("Updload dataset to OpenAI")
    stream_dataset.seek(0)
    dataset_file: FileObject = client.files.create(file=stream_dataset, purpose="assistants")

    logger.info("Create task for model")
    thread: Thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="""In separate first message:
        Provide short overview for features in dataset.
        Choose best candidate for target in ML task among columns.
        Response me with conclusion.
        """,
    )

    logger.info("Create assistent for working with dataset")
    eda_assistant: Assistant = client.beta.assistants.create(
        instructions="""You are an excellent senior Data Scientist with 10 years of experience.
        You make Exploratory Data Analysis for recieved datasets.
        Probably dataset will be in csv format.
        Give anwser on russian except of column names or terms.
        Give answer in correct Markdown format (use only Markdown's secial symbols), 
        which can be pretty displayed in Telegram message.
        """,
        model="gpt-4o",
        tools=[{"type": "code_interpreter"}],
        tool_resources={"code_interpreter": {"file_ids": [dataset_file.id]}},
    )

    logger.info("Process dataset")
    await update.message.reply_text(text="Обрабатываем датасет")
    for text in gen_messages_from_eda_stream(thread=thread, eda_assistant=eda_assistant):
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="""In separate second message:
        Construct new features based solely on the columns present in the dataset.

        In your response:
        0. Header
        1. Enumerate the features you suggest adding.
        2. For each feature, provide a formula using the existing columns of the dataset.
        3. Explain why each feature would be beneficial for an ML model.

        Important constraints:
        - Use only the columns contained in the dataset.
        - Do not suggest collecting additional data or adding anything that cannot be calculated from the existing columns.
        - Respond with the list of new features, formulae, and explanations without any welcoming or accompanying text.
        - You have not seen the data yet, so do not construct features based on concrete names of categories.
        """,
    )
    for text in gen_messages_from_eda_stream(thread=thread, eda_assistant=eda_assistant):
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

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
    file = None
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
    if (
        update.message.effective_attachment
        and type(update.message.effective_attachment) is Document
        and update.message.effective_attachment.mime_type
        and update.message.effective_attachment.mime_type.startswith("image/")
    ):
        file = await update.message.effective_attachment.get_file()
    if file is None:
        return MEME_EXPL
    await update.message.reply_text(text="Анализируем мем...")
    data = await file.download_as_bytearray()
    explanation = explain_meme(data, context)
    keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
    await update.message.reply_text(
        text=f"{explanation}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return MEME_EXPL_DIALOG


def explain_meme(image: bytearray, context: CallbackContext) -> str:
    """Объяснить мем по изображению."""
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    bytes_data = bytes(image)
    base64_encoded = base64.b64encode(bytes_data)
    base64_string = base64_encoded.decode("utf-8")
    dialog_context = DialogContext(
        model="gpt-4o",
        max_tokens=1024,
        temperature=0.5,
    )
    context.user_data["dialog"] = dialog_context
    dialog_context.messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Представь, что ты столкнулся с мемом, который вызывает у тебя смех. Важно не описать
                     картинку, а понять, почему этот мем смешной. Ответь коротко на следующие вопросы: Какие элементы
                     мема вызывают смех? Какая основная идея или шутка заложена в меме? Есть ли какие-либо культурные
                     или интернет-отсылки, которые следует знать, чтобы понять мем? Ответ не структурируй.""",
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
    return send_to_open_ai(dialog_context)


def send_to_open_ai(dialog_context: DialogContext) -> str:
    """Отправить контекст диалога в OpenAI."""
    response: ChatCompletion = client.chat.completions.create(
        model=dialog_context.model,
        messages=dialog_context.messages,
        max_tokens=dialog_context.max_tokens,
        temperature=dialog_context.temperature,
    )
    content = response.choices[0].message.content
    if content is None:
        logger.error("OpenAI содержит пустой ответ")
        return ""
    dialog_context.messages.append(response.choices[0].message)
    return content.strip()


async def dialog(update: Update, context: CallbackContext) -> int:
    """Хэндлер диалога."""
    if update.message is None:
        raise BadArgumentError(MESSAGE_ARG)
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    context.user_data["dialog"].messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": update.message.text,
                },
            ],
        },
    )
    response = send_to_open_ai(context.user_data["dialog"])
    await update.message.reply_text(text=response)
    return DIALOG


async def meme_explanation_dialog(update: Update, context: CallbackContext) -> int:
    """Хэндлер диалога объяснения мема."""
    if update.message is None:
        raise BadArgumentError(MESSAGE_ARG)
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    context.user_data["dialog"].messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": update.message.text,
                },
            ],
        },
    )
    response = send_to_open_ai(context.user_data["dialog"])

    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    if update.effective_chat is None:
        raise BadArgumentError(EFFECTIVE_CHAT_ARG)
    keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
    await update.message.reply_text(text=response, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return MEME_EXPL_DIALOG


async def finish_dialog(update: Update, context: CallbackContext) -> int:
    """Хэндлер завершения диалога."""
    if update.message is None:
        raise BadArgumentError(MESSAGE_ARG)
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    await update.message.reply_text(
        text="Диалог завершен",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data["dialog"] = None
    return await start(update, context)


async def remove_chat_buttons(
    update: Update,
    context: CallbackContext,
    msg_text: str = "-",
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


async def handle_user_reply(update: Update, context: CallbackContext) -> None:
    """обработка  ответа от пользователя."""
    if update.message is None:
        raise BadArgumentError(MESSAGE_ARG)
    if update.message.voice:
        audio_file = await context.bot.get_file(update.message.voice.file_id)

        audio_bytes = BytesIO(await audio_file.download_as_bytearray())

        transcription = generate_transcription(audio_bytes)

        reply = generate_response(transcription)
        await update.message.reply_text(reply)

        logger.info("user:", audio_file.file_path)
        logger.info("transcription:", transcription)
        logger.info("assistant:", reply)

    if update.message.text:
        reply = generate_response(update.message.text)
        await update.message.reply_text(reply)


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
        CODE_HELP: [CallbackQueryHandler(code_help)],
        TASK_HELP: [CallbackQueryHandler(task_help)],
        HELP_FACTORY: [CallbackQueryHandler(task_help), MessageHandler(filters.TEXT, help_factory)],
        EDA: [CallbackQueryHandler(eda), MessageHandler(filters.ATTACHMENT, eda), CommandHandler("start", start)],
        USER_REPLY: [MessageHandler(filters.VOICE | filters.TEXT, handle_user_reply)],
        MEME_EXPL: [
            CallbackQueryHandler(meme_explanation),
            MessageHandler(filters.PHOTO, meme_explanation),
            MessageHandler(filters.ATTACHMENT, meme_explanation),
            CommandHandler("start", start),
        ],
        MEME_EXPL_DIALOG: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, meme_explanation_dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
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
