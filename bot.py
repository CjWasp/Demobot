import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from handlers import registration, lessons, homework, admin

logging.basicConfig(level=logging.INFO)


async def main():
    db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Order matters: homework before lessons (both handle hw_start callback)
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(homework.router)
    dp.include_router(lessons.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
