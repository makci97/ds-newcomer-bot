from telegram.ext import Application

from .tokens import TELEGRAM_BOT_TOKEN


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([('start', 'Запускает бота')])


# Создание экземпляра бота
application: Application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
