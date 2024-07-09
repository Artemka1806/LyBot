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
from apscheduler.schedulers.background import BackgroundScheduler
from mongoengine import connect
from dotenv import load_dotenv
import redis
import requests

from middlewares import *
from handlers import login, attendance, schedule, donation
from models.user import User
from keyboards import main_menu

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
MONGO_URI = getenv("MONGO_URI")
REDIS_URL = getenv("REDIS_URL")
API_URL = getenv("API_URL")

connect(host=MONGO_URI)

r = redis.Redis.from_url(url=REDIS_URL)

storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)

for middleware in OUTER_MIDDLEWARES:
	dp.update.outer_middleware(middleware())
dp.message.middleware(MenuMiddleware())
dp.include_routers(login.router, attendance.router, schedule.router, donation.router)

dp.message.filter(F.chat.type == "private")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


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
	scheduler = BackgroundScheduler()
	scheduler.configure(timezone="Europe/Kyiv")
	scheduler.add_job(save_api_data, 'interval', minutes=5)
	scheduler.start()
	try:
		await dp.start_polling(bot)
	finally:
		scheduler.shutdown()
		await bot.session.close()


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, stream=sys.stdout)
	asyncio.run(main())
