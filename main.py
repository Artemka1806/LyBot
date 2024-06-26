import asyncio
import logging
from os import getenv
import sys
from typing import Type

from aiogram import Bot, Dispatcher, html, F, flags
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, MagicData
from aiogram.types import Message, Update
from mongoengine import connect
from dotenv import load_dotenv
from fastapi import FastAPI

from middlewares import auth, extra_data, menu
from handlers import login, attendance
from models.user import User
from keyboards import main_menu

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
MONGO_URI = getenv("MONGO_URI")

WEBHOOK_PATH = f"/bot/{TOKEN}"
WEBHOOK_URL = getenv("WEBHOOK_URL_BASE") + WEBHOOK_PATH

dp = Dispatcher()
dp.update.outer_middleware(auth.AuthMiddleware())
dp.update.outer_middleware(extra_data.ExtraDataMiddleware())
dp.message.middleware(menu.MenuMiddleware())
dp.include_routers(login.router, attendance.router)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

connect(host=MONGO_URI)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL
        )


@app.on_event("shutdown")
async def on_shutdown():
    await bot.get_session().close()


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = Update(**update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(telegram_update)


@app.get("/")
def main_web_handler():
    return "Everything ok!"


@dp.message(CommandStart(), MagicData(F.user))
async def start_command_handler(message: Message, user: Type) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!", reply_markup=main_menu.keyboard(user))


@dp.message(Command("deleteme"))
async def deleteme_command_handler(message: Message) -> None:
    users = User.objects(tg_id=message.from_user.id)
    if users:
        users.first().delete()
        await message.answer("Deleted!")
    else:
        await message.answer("Already deleted!")


@dp.message(Command("waltz"))
@flags.show_main_menu
async def waltz_command_handler(message: Message) -> None:
    await message.answer("""Bring out the charge of the love brigade
There is spring in the air once again
Drink to the sound of the song parade
There is music and love everywhere
Give a little love to me (I want it)
Take a little love from me
I wanna share it with you
I feel like a millionaire""")


async def main() -> None:
    await dp.start_polling(bot, polling_timeout=25)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
