import asyncio
import json
import logging
from os import getenv
import sys
import time
from typing import Type

from aiogram import Bot, Dispatcher, html, F, flags
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, MagicData
from aiogram.types import Message
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import requests

from middlewares import *
from handlers import ROUTERS
from models.common import instance
from keyboards import main_menu
from middlewares.throttlinig import ThrottlingMiddleware
from utils.change_users_status import change_users_status
from utils.bulk_mailing import bulk_mailing

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
TEST_TOKEN = getenv("TEST_BOT_TOKEN")
USE_TEST_SERVER = getenv("USE_TEST_SERVER")
MONGO_URI = getenv("MONGO_URI")
REDIS_URL = getenv("REDIS_URL")
API_URL = getenv("API_URL")
ERROR_LOG_CHAT_ID = getenv("ERROR_LOG_CHAT_ID")

client = AsyncIOMotorClient(MONGO_URI)
db = client.data
instance.set_db(db)

r = redis.Redis.from_url(url=REDIS_URL)

storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)
dp.message.outer_middleware(ThrottlingMiddleware(storage=storage))
dp.message.outer_middleware(TypingActionMiddleware())
for middleware in OUTER_MIDDLEWARES:
	dp.update.outer_middleware(middleware())
dp.message.middleware(MenuMiddleware())
dp.include_routers(*ROUTERS)


main_bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
test_bot = Bot(token=TEST_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

bot = test_bot if USE_TEST_SERVER == "1" else main_bot


@dp.message(CommandStart(), MagicData(F.user))
async def start_command_handler(message: Message, user: Type) -> None:
	await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!", reply_markup=main_menu.keyboard(user))


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


@dp.message(Command("error"))
@flags.show_main_menu
async def error_command_handler(message: Message) -> None:
	raise Exception("Love Of My Life\nhttps://youtu.be/sUJkCXE4sAA")


def save_api_data():
	data = requests.get(API_URL + "/api/schedule").json()
	r.set("schedule", json.dumps(data[0]["Schedule"]))
	r.set("bells", json.dumps(data[0]["ScheduleBell"]))
	r.set("extra", json.dumps(data[0]["ExtraClasses"]))
	r.set("time_managment", json.dumps(data[0]["TimeManagementData"]))
	r.set("last_save", int(time.time()))


async def main():
	if getenv("DISABLE_SCHEDULER") is None:
		from apscheduler.schedulers.background import BackgroundScheduler
		from apscheduler.schedulers.asyncio import AsyncIOScheduler
		scheduler = BackgroundScheduler()
		scheduler.configure(timezone="Europe/Kyiv")
		scheduler.add_job(save_api_data, 'interval', minutes=5)
		scheduler.start()
		aioscheduler = AsyncIOScheduler()
		aioscheduler.configure(timezone="Europe/Kyiv")
		aioscheduler.add_job(change_users_status, "cron", hour=20, minute=0)
		aioscheduler.add_job(bulk_mailing, "cron", hour=8, minute=5, args=[bot, "Не забудьте змінити свій статус", ERROR_LOG_CHAT_ID])
		aioscheduler.start()
	try:
		await bot.delete_webhook(drop_pending_updates=True)
		await dp.start_polling(bot)
	finally:
		if getenv("DISABLE_SCHEDULER") is None:
			scheduler.shutdown()
		await bot.session.close()


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, stream=sys.stdout)
	asyncio.run(main())
