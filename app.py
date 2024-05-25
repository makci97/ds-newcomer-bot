import io
from io import BytesIO
from typing import TYPE_CHECKING

from loguru import logger
from openai.types.beta.threads import MessageCreateParams
from telegram import (
    Document,
    File,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
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
from utils.constants import MAX_TOKENS, TEMPERATURE, CodePromptMode, ModelName, TaskPromptMode
from utils.dialog_context import DialogContext
from utils.helpers import check_user_settings, gen_messages_from_eda_stream, single_text2text_query, text_splitter
from utils.prompts import (
    AlgoTaskMakerPrompt,
    CodePrompt,
    GenericUserTextPrompt,
    InterviewMakerPrompt,
    MemeImagePrompt,
    MemeNeedReactionPrompt,
    MLTaskMakerPrompt,
    Prompt,
    PsychoHelpPrompt,
    RoadMapMakerPrompt,
    TaskPrompt,
    TestMakerPrompt,
)
from utils.utils import print_message

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
    MEME_NEED_REACT,
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
    ALGO_DIALOG,
    ML_DIALOG,
    INTERVIEW_DIALOG,
    TEST_MAKER,
    ROADMAP_MAKER,
    PSYCHO_HELP,
) = range(29)

CALLBACK_QUERY_ARG = "update.callback_query"
MESSAGE_ARG = "update.message"
EFFECTIVE_CHAT_ARG = "update.effective_chat"
USER_DATA_ARG = "context.user_data"
LAST_MENU_MESSAGE = "last_menu_message"


async def start(update: Update, context: CallbackContext) -> int:
    """Начальный хэндлер дерева команд."""
    await deactivate_last_menu_button(context)
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
    message = None
    if update.message:  # When /start command is used
        message = await update.message.reply_text("Выберите задачу:", reply_markup=reply_markup)
    elif update.callback_query:
        message = await update.callback_query.edit_message_text(  # type: ignore[assignment]
            "Выберите задачу:",
            reply_markup=reply_markup,
        )
    if message and type(message) is Message:
        context.user_data[LAST_MENU_MESSAGE] = message
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
            [InlineKeyboardButton("Создай тест", callback_data="TEST_MAKER")],
            [InlineKeyboardButton("ROADMAP", callback_data="ROADMAP_MAKER")],
            [InlineKeyboardButton("Психологическая помощь", callback_data="PSYCHO_HELP")],
            [InlineKeyboardButton("Настройки пользователя", callback_data="USER_SETTINGS")],
            [InlineKeyboardButton("Назад", callback_data="BACK")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Ты выбрал прокачку знаний.\n"
            "В этих сценариях ты можешь отвечать как в текстовом, так и в аудиоформате:",
            reply_markup=reply_markup,
        )
        return KNOWLEDGE_GAIN
    if choice == "PROBLEM_SOL":
        keyboard = [
            [InlineKeyboardButton("Скину описание задачи", callback_data="TASK_HELP")],
            [InlineKeyboardButton("Скину код", callback_data="CODE_HELP")],
            [InlineKeyboardButton("Скину датасет", callback_data="EDA")],
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
    if "interview_hard" not in context.user_data:  # type: ignore  # noqa: PGH003
        context.user_data["interview_hard"] = "JUNIOR"  # type: ignore  # noqa: PGH003
    if "questions_hard" not in context.user_data:  # type: ignore  # noqa: PGH003
        context.user_data["questions_hard"] = "EASY"  # type: ignore  # noqa: PGH003
    if query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    await query.answer()
    choice = query.data
    if choice == "INTERVIEW_PREP" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        context.user_data["dialog"] = []  # type: ignore  # noqa: PGH003
        context.user_data["topic"] = ""  # type: ignore  # noqa: PGH003
        keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,  # type: ignore  # noqa: PGH003
            text=f"Уровень подготовки:"
            f"{context.user_data['interview_hard']}\nУровень заданий:"  # type: ignore  # noqa: PGH003
            f"{context.user_data['questions_hard']}\nНа какую тему будет собеседование?",
            # type: ignore  # noqa: PGH003
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        )
        return INTERVIEW_DIALOG
    if choice == "ALGO_TASK" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        context.user_data["dialog"] = []  # type: ignore  # noqa: PGH003
        context.user_data["topic"] = ""  # type: ignore  # noqa: PGH003
        keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,  # type: ignore  # noqa: PGH003
            text=f"Уровень подготовки:"
            f"{context.user_data['interview_hard']}\nУровень заданий:"  # type: ignore  # noqa: PGH003
            f"{context.user_data['questions_hard']}\nНа какую тему хочешь задачу?",  # type: ignore  # noqa: PGH003
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),  # type: ignore[arg-type]
        )
        return ALGO_DIALOG
    if choice == "ML_TASK" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        context.user_data["dialog"] = []  # type: ignore  # noqa: PGH003
        context.user_data["topic"] = ""  # type: ignore  # noqa: PGH003
        keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,  # type: ignore  # noqa: PGH003
            text=f"Уровень подготовки: "
            f"{context.user_data['interview_hard']}\nУровень заданий: "  # type: ignore  # noqa: PGH003
            f"{context.user_data['questions_hard']}\nНа какую тему хочешь задачу?",  # type: ignore  # noqa: PGH003
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),  # type: ignore[arg-type]
        )
        return ML_DIALOG
    if choice == "TEST_MAKER" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        context.user_data["dialog"] = []  # type: ignore  # noqa: PGH003
        context.user_data["topic"] = ""  # type: ignore  # noqa: PGH003
        keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,  # type: ignore  # noqa: PGH003
            text=f"Уровень подготовки: "
            f"{context.user_data['interview_hard']}\nУровень заданий: "  # type: ignore  # noqa: PGH003
            f"{context.user_data['questions_hard']}\nНа какую тему хочешь тест?",  # type: ignore  # noqa: PGH003
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),  # type: ignore[arg-type]
        )
        return TEST_MAKER
    if choice == "ROADMAP_MAKER" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        context.user_data["dialog"] = []  # type: ignore  # noqa: PGH003
        context.user_data["topic"] = ""  # type: ignore  # noqa: PGH003
        keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,  # type: ignore  # noqa: PGH003
            text=f"Уровень подготовки: "
            f"{context.user_data['interview_hard']}\nУровень заданий: "  # type: ignore  # noqa: PGH003
            f"{context.user_data['questions_hard']}\nНа какую тему хочешь RoadMap?",
            # type: ignore  # noqa: PGH003
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),  # type: ignore[arg-type]
        )
        return ROADMAP_MAKER
    if choice == "PSYCHO_HELP" and check_user_settings(context):
        if update.callback_query is None:
            raise BadArgumentError(CALLBACK_QUERY_ARG)
        context.user_data["dialog"] = []  # type: ignore  # noqa: PGH003
        context.user_data["topic"] = ""  # type: ignore  # noqa: PGH003
        keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,  # type: ignore  # noqa: PGH003
            text="Чем могу помочь?",  # type: ignore  # noqa: PGH003
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),  # type: ignore[arg-type]
        )
        return PSYCHO_HELP
    if choice == "USER_SETTINGS":
        keyboard = [
            [InlineKeyboardButton("Уровень подготовки", callback_data="INTERVIEW_HARD")],  # type: ignore  # noqa: PGH003
            [InlineKeyboardButton("Сложность заданий", callback_data="QUESTIONS_HARD")],  # type: ignore  # noqa: PGH003
            [InlineKeyboardButton("BACK", callback_data="BACK")],  # type: ignore  # noqa: PGH003
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)  # type: ignore  # noqa: PGH003
        await query.edit_message_text(text="Настройки:", reply_markup=reply_markup)
        return USER_SETTINGS
    if choice == "BACK":
        return await start(update, context)
    raise BadChoiceError(choice)  # type: ignore  # noqa: PGH003


async def problem_solving(update: Update, context: CallbackContext) -> int:
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
    for text_chunk in text_splitter(text=explanation):
        await update.message.reply_text(text=text_chunk, parse_mode=ParseMode.MARKDOWN)
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

    logger.info("Create assistent for working with dataset")
    eda_assistant: Assistant = client.beta.assistants.create(
        instructions="""You are an excellent senior Data Scientist with 10 years of experience.
        You make Exploratory Data Analysis for recieved datasets.
        Probably dataset will be in csv format.

        Output formatting:
        - Give anwser on russian except of column names or terms. It's important!
        - Give answer in correct Markdown format (use only Markdown's secial symbols)
        - For all headers use Telegram's "*bold*", and `code` formatiing
        instead of Markdown's "#", "##"
        - Must be possible to pretty display answer in Telegram message
        - Don't use tables in response
        """,
        model="gpt-4o",
        tools=[{"type": "code_interpreter"}],
        tool_resources={"code_interpreter": {"file_ids": [dataset_file.id]}},
    )

    logger.info("Create task for model")
    messages: list[MessageCreateParams] = [
        MessageCreateParams(
            role="user",
            content="""In separate first message:
        Provide short overview for features in dataset.
        Choose best candidate for target (the most useful info for business) in ML task among columns.
        Response me with conclusion.
        """,
        ),
    ]
    thread: Thread = client.beta.threads.create(messages=messages)

    logger.info("Process dataset")
    await update.message.reply_text(text="Обрабатываем датасет (30-60 секунд)")
    for text in gen_messages_from_eda_stream(thread=thread, eda_assistant=eda_assistant):
        messages.append(MessageCreateParams(role="assistant", content=text))
        await print_message(message=update.message, text=text, parse_mode=ParseMode.MARKDOWN)

    messages.append(
        MessageCreateParams(
            role="user",
            content="""In separate second message:
        Construct new features based solely on the columns present in the dataset.
        Features have to be correlated with target, but can't use target.

        In your response:
        0. Header
        1. Enumerate the features you suggest adding.
        2. For each feature, provide a formula using the existing columns of the dataset.
        3. Explain why each feature would be beneficial for an ML model.

        Important constraints:
        - Use only the columns contained in the dataset.
        - Do not suggest collecting additional data or
          adding anything that cannot be calculated from the existing columns.
        - Respond with the list of new features, formulae, and explanations without any welcoming or accompanying text.
        - You have not seen the data yet, so do not construct features based on concrete names of categories.
        """,
        ),
    )
    thread = client.beta.threads.create(messages=messages)
    for text in gen_messages_from_eda_stream(thread=thread, eda_assistant=eda_assistant):
        await print_message(message=update.message, text=text, parse_mode=ParseMode.MARKDOWN)

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
    await update.message.reply_text(text="Изучаю мем...")
    data = await file.download_as_bytearray()
    explanation = explain_meme(data, context)
    finish_dialog_keyboard = [[KeyboardButton("/finish_dialog")]]  # type: ignore[list-item]
    await update.message.reply_text(
        text=f"{explanation}",
        reply_markup=ReplyKeyboardMarkup(finish_dialog_keyboard, resize_keyboard=True),
    )
    need_react_keyboard = [
        [InlineKeyboardButton("Да", callback_data="NEED_MEME_REACTION_YES")],
        [InlineKeyboardButton("Нет", callback_data="NEED_MEME_REACTION_NO")],
    ]
    await update.message.reply_text(
        text="Подсказать, как смешно ответить?",
        reply_markup=InlineKeyboardMarkup(need_react_keyboard),
    )
    return MEME_NEED_REACT


async def meme_need_reaction(update: Update, context: CallbackContext) -> int:
    """Хэндлер вопроса, нужно ли сгенерировать реакцию на мем."""
    if update.callback_query is None:
        raise BadArgumentError(CALLBACK_QUERY_ARG)
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    if update.callback_query.data == "NEED_MEME_REACTION_YES":
        message = await update.callback_query.edit_message_text("Ок, генерирую ответ...")
        context.user_data["dialog"].messages.append(*MemeNeedReactionPrompt().messages)
        response = send_to_open_ai(context.user_data["dialog"])
        await message.edit_text(response)  # type: ignore   # noqa: PGH003
    else:
        await update.callback_query.edit_message_text("Ок, не генерирую ответ")
    return MEME_EXPL_DIALOG


def explain_meme(image: bytearray, context: CallbackContext) -> str:
    """Объяснить мем по изображению."""
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)

    dialog_context = DialogContext(
        model="gpt-4o",
        max_tokens=1024,
        temperature=0.5,
    )
    context.user_data["dialog"] = dialog_context
    dialog_context.messages.append(*MemeImagePrompt(image=image).messages)
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


async def algo_dialog(update: Update, context: CallbackContext) -> int:
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
        context.user_data["dialog"].append({"role": "user", "content": text})

    prompt: AlgoTaskMakerPrompt = AlgoTaskMakerPrompt(
        questions_hard=context.user_data["questions_hard"],
        interview_hard=context.user_data["interview_hard"],
        topic=context.user_data["topic"],
        reply=context.user_data["dialog"],
    )
    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    logger.debug(explanation)
    for text_chunk in text_splitter(text=explanation):
        await update.message.reply_text(text=text_chunk, parse_mode=ParseMode.MARKDOWN)
    return ALGO_DIALOG


async def ml_dialog(update: Update, context: CallbackContext) -> int:
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
        context.user_data["dialog"].append({"role": "user", "content": text})

    prompt: MLTaskMakerPrompt = MLTaskMakerPrompt(
        questions_hard=context.user_data["questions_hard"],
        interview_hard=context.user_data["interview_hard"],
        topic=context.user_data["topic"],
        reply=context.user_data["dialog"],
    )
    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    logger.debug(explanation)
    for text_chunk in text_splitter(text=explanation):
        await update.message.reply_text(text=text_chunk, parse_mode=ParseMode.MARKDOWN)
    return ML_DIALOG


async def interview_dialog(update: Update, context: CallbackContext) -> int:
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
        context.user_data["dialog"].append({"role": "user", "content": text})

    prompt: InterviewMakerPrompt = InterviewMakerPrompt(
        questions_hard=context.user_data["questions_hard"],
        interview_hard=context.user_data["interview_hard"],
        topic=context.user_data["topic"],
        reply=context.user_data["dialog"],
    )
    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    for text_chunk in text_splitter(text=explanation):
        await update.message.reply_text(text=text_chunk, parse_mode=ParseMode.MARKDOWN)
    return INTERVIEW_DIALOG


async def test_dialog(update: Update, context: CallbackContext) -> int:
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
        context.user_data["dialog"].append({"role": "user", "content": text})

    prompt: TestMakerPrompt = TestMakerPrompt(
        questions_hard=context.user_data["questions_hard"],
        interview_hard=context.user_data["interview_hard"],
        topic=context.user_data["topic"],
        reply=context.user_data["dialog"],
    )
    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    for text_chunk in text_splitter(text=explanation):
        await update.message.reply_text(text=text_chunk, parse_mode=ParseMode.MARKDOWN)
    return TEST_MAKER


async def roadmap_dialog(update: Update, context: CallbackContext) -> int:
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
        context.user_data["dialog"].append({"role": "user", "content": text})

    prompt: RoadMapMakerPrompt = RoadMapMakerPrompt(
        questions_hard=context.user_data["questions_hard"],
        interview_hard=context.user_data["interview_hard"],
        topic=context.user_data["topic"],
        reply=context.user_data["dialog"],
    )
    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    for text_chunk in text_splitter(text=explanation):
        await update.message.reply_text(text=text_chunk, parse_mode=ParseMode.MARKDOWN)
    return ROADMAP_MAKER


async def psyho_dialog(update: Update, context: CallbackContext) -> int:
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

    context.user_data["dialog"].append({"role": "user", "content": text})

    prompt: PsychoHelpPrompt = PsychoHelpPrompt(
        reply=context.user_data["dialog"],
    )
    explanation: str = single_text2text_query(
        model=ModelName.GPT_4O,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    for text_chunk in text_splitter(text=explanation):
        await update.message.reply_text(text=text_chunk, parse_mode=ParseMode.MARKDOWN)
    return PSYCHO_HELP


async def meme_explanation_dialog(update: Update, context: CallbackContext) -> int:
    """Хэндлер диалога объяснения мема."""
    if update.message is None or update.message.text is None:
        raise BadArgumentError(MESSAGE_ARG)
    if context.user_data is None:
        raise BadArgumentError(USER_DATA_ARG)
    messages = GenericUserTextPrompt(text=update.message.text).messages  # type: ignore[arg-type]
    context.user_data["dialog"].messages.append(*messages)
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
        text="Рад был помочь",
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


async def deactivate_last_menu_button(context: CallbackContext) -> None:
    """Прячет кнопки из последнего сообщения-меню из context.user_data[LAST_MENU_MESSAGE]."""
    if (
        context.user_data is None
        or LAST_MENU_MESSAGE not in context.user_data
        or context.user_data[LAST_MENU_MESSAGE] is None
    ):
        return
    await context.user_data[LAST_MENU_MESSAGE].edit_reply_markup(reply_markup=None)


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
        CODE_HELP: [CallbackQueryHandler(code_help)],
        TASK_HELP: [CallbackQueryHandler(task_help)],
        HELP_FACTORY: [CallbackQueryHandler(task_help), MessageHandler(filters.TEXT, help_factory)],
        EDA: [CallbackQueryHandler(eda), MessageHandler(filters.ATTACHMENT, eda), CommandHandler("start", start)],
        MEME_EXPL: [
            CallbackQueryHandler(meme_explanation),
            MessageHandler(filters.PHOTO, meme_explanation),
            MessageHandler(filters.ATTACHMENT, meme_explanation),
            CommandHandler("start", start),
        ],
        MEME_NEED_REACT: [
            CallbackQueryHandler(meme_need_reaction),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
        MEME_EXPL_DIALOG: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, meme_explanation_dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
        ALGO_DIALOG: [
            MessageHandler(~filters.COMMAND, algo_dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
        ML_DIALOG: [
            MessageHandler(~filters.COMMAND, ml_dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
        INTERVIEW_DIALOG: [
            MessageHandler(~filters.COMMAND, interview_dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
        TEST_MAKER: [
            MessageHandler(~filters.COMMAND, test_dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
        ROADMAP_MAKER: [
            MessageHandler(~filters.COMMAND, roadmap_dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
        PSYCHO_HELP: [
            MessageHandler(~filters.COMMAND, psyho_dialog),
            CommandHandler("start", start),
            CommandHandler("finish_dialog", finish_dialog),
        ],
    },
    fallbacks=[CommandHandler("start", start)],
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler("start", start))

# Запуск бота
application.run_polling()
