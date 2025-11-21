from aiogram import Bot, Dispatcher
from chatting import *
from hehbot.env_service import bot, dp, env
import os

import warnings
# Ігнорування попереджень UserWarning
warnings.filterwarnings("ignore", category=UserWarning)

# Головна асинхронна функція для запуску бота
async def main() -> None:
    await BotCommand.initialize_embeddings()
    await bot.delete_webhook(True)
    await dp.start_polling(bot)


import asyncio
import logging
import sys


def ensure_dir(path: str) -> str:
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        os.makedirs(abs_path, exist_ok=True)
    return abs_path

if __name__ == "__main__":
    ensure_dir('img/changed_credit')
    ensure_dir('img/credits')
    ensure_dir('img/slot_machine/users')
    ensure_dir('img/history')
    ensure_dir('img/history/users')
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
