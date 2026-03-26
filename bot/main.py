import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from core.config import settings
from bot.handlers import start, kyc, order_flow, admin_panel

logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    """Регистрируем команды бота."""
    # Ukrainian
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Почати"),
            BotCommand(command="order", description="Нова заявка"),
            BotCommand(command="status", description="Мої заявки"),
            BotCommand(command="lang", description="Мова інтерфейсу"),
            BotCommand(command="admin", description="Адмін-панель"),
        ],
        language_code="uk",
    )

    # English
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start"),
            BotCommand(command="order", description="New order"),
            BotCommand(command="status", description="My orders"),
            BotCommand(command="lang", description="Language"),
            BotCommand(command="admin", description="Admin panel"),
        ],
        language_code="en",
    )


async def main():
    if not settings.TG_TOKEN:
        raise RuntimeError("TG_TOKEN is not set in environment or .env file")

    bot = Bot(
        token=settings.TG_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(start.router)
    dp.include_router(kyc.router)
    dp.include_router(order_flow.router)
    dp.include_router(admin_panel.router)

    await on_startup(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
