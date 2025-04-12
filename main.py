import asyncio
import json
import logging
from os import getenv
import sys
import time
import re
from typing import Type, Annotated, Dict, Any, Optional
from urllib import parse

import aiohttp
from aiogram import Bot, Dispatcher, html, F, flags
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, MagicData
from aiogram.types import Message
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.methods import SetWebhook
from aiogram.types import Update
from aiohttp import web
from dotenv import load_dotenv
from fastapi import FastAPI, Form, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from marshmallow.exceptions import ValidationError
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
import redis
import requests
import uvicorn

from middlewares import *
from handlers import ROUTERS
from models.common import instance
from models.user import User
from keyboards import main_menu
from middlewares.throttlinig import ThrottlingMiddleware
from utils.change_users_status import change_users_status
from utils.bulk_mailing import bulk_mailing

load_dotenv()

# Bot configuration
TOKEN = getenv("BOT_TOKEN")
TEST_TOKEN = getenv("TEST_BOT_TOKEN")
USE_TEST_SERVER = getenv("USE_TEST_SERVER")
MONGO_URI = getenv("MONGO_URI")
REDIS_URL = getenv("REDIS_URL")
API_URL = getenv("API_URL")
ERROR_LOG_CHAT_ID = getenv("ERROR_LOG_CHAT_ID")

# Webhook configuration
WEBHOOK_HOST = getenv("WEBHOOK_HOST")
WEBHOOK_PATH = getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_PATH_TEST = getenv("WEBHOOK_PATH_TEST", "/webhook_test")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBHOOK_URL_TEST = f"{WEBHOOK_HOST}{WEBHOOK_PATH_TEST}"

TG_ELECTION_BOT_TOKEN = getenv("TG_ELECTION_BOT_TOKEN")
TG_ELECTION_GROUP_ID = getenv("TG_ELECTION_GROUP_ID")

# MongoDB setup
client = AsyncIOMotorClient(MONGO_URI)
db = client.data
instance.set_db(db)

# Redis setup
r = redis.Redis.from_url(url=REDIS_URL)

# Bot initialization
main_bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
test_bot = Bot(token=TEST_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot = test_bot if USE_TEST_SERVER == "1" else main_bot

# FastAPI app initialization
app = FastAPI()

# Configure CORS for API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Aiogram Dispatcher setup
storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)
dp.message.outer_middleware(ThrottlingMiddleware(storage=storage))
dp.message.outer_middleware(TypingActionMiddleware())
for middleware in OUTER_MIDDLEWARES:
    dp.update.outer_middleware(middleware())
dp.message.middleware(MenuMiddleware())
dp.message.middleware(AdMiddleware())
dp.include_routers(*ROUTERS)


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


@dp.message(Command("phid"), F.photo)
@flags.show_main_menu
async def get_photo_id_handler(message: Message) -> None:
    await message.answer(f"{message.photo[-1].file_id}")


def save_api_data():
    data = requests.get(API_URL + "/api/schedule").json()
    r.set("schedule", json.dumps(data[0]["Schedule"]))
    r.set("bells", json.dumps(data[0]["ScheduleBell"]))
    r.set("extra", json.dumps(data[0]["ExtraClasses"]))
    r.set("time_managment", json.dumps(data[0]["TimeManagementData"]))
    r.set("last_save", int(time.time()))


async def send_reminder():
    current_day_of_week = time.localtime().tm_wday
    if current_day_of_week < 5:
        await bulk_mailing(bot, "Не забудьте змінити свій статус", ERROR_LOG_CHAT_ID)


# API Endpoints (from LyBotAPI)
class ElectionFormData(BaseModel):
    name: str
    email: str
    question: str


@app.head("/")
@app.get("/")
async def index():
    """
    Why not?
    """
    return {"text": "I don't think you're supposed to be here."}


@app.get("/attendance")
async def get_attendance(timestamp: float = -1.0):
    # Query users with updated status after the given timestamp
    data = []
    for doc in await User.find({"status_updated_at": {"$gt": timestamp}}).to_list(length=None):
        d = doc.to_mongo()
        data.append(d)

    data = sorted(data, key=lambda x: x.get('family_name', ''))
    result = {}

    for entry in data:
        # Get group information
        group = entry.get("group")
        if group is None:
            continue
            
        # Get class number (first part of group) and subgroup (full group name)
        class_num = group.split('-')[0]
        subgroup = group
        
        # Create nested dictionaries for classes and groups if they don't exist
        if class_num not in result:
            result[class_num] = {}
        if subgroup not in result[class_num]:
            result[class_num][subgroup] = {}
            
        # Format the user's full name
        full_name = f"{entry.get('family_name', '')} {entry.get('given_name', '')}"
        
        # Create object for each student using dictionary attributes
        # Store with full_name as the key for backward compatibility
        result[class_num][subgroup][full_name] = {
            "name": full_name,
            "avatar_url": entry.get("avatar_url", ""),
            "status_updated_at": entry.get("status_updated_at"),
            "status": entry.get("status", 3),
            "message": entry.get("status_message", "")
        }
    
    # Function for sorting subgroups by numerical and alphabetical parts
    def sort_key(subgroup):
        match = re.match(r"(\d+)-([А-Яа-я])", subgroup)
        if match:
            return (int(match.group(1)), match.group(2))
        return (0, subgroup)
    
    # Sort classes and subgroups
    sorted_result = {
        class_num: dict(sorted(result[class_num].items(), key=lambda x: sort_key(x[0])))
        for class_num in sorted(result.keys(), key=int)
    }
    
    return sorted_result


# Telegram webhook handlers
@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    """Handle webhook updates for main bot"""
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": main_bot})
    await dp.feed_update(bot=main_bot, update=update)
    return {"ok": True}


@app.post(WEBHOOK_PATH_TEST)
async def webhook_test_handler(request: Request):
    """Handle webhook updates for test bot"""
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": test_bot})
    await dp.feed_update(bot=test_bot, update=update)
    return {"ok": True}


async def on_startup():
    # Set up webhooks for bots
    await main_bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    await test_bot.set_webhook(url=WEBHOOK_URL_TEST, drop_pending_updates=True)

    # Set up schedulers
    if getenv("DISABLE_SCHEDULER") is None:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.configure(timezone="Europe/Kyiv")
        scheduler.add_job(save_api_data, 'interval', minutes=5)
        scheduler.add_job(change_users_status, "cron", hour=20, minute=0)
        scheduler.add_job(send_reminder, "cron", hour=8, minute=5)
        scheduler.start()


async def on_shutdown():
    # Remove webhooks
    await main_bot.delete_webhook()
    await test_bot.delete_webhook()
    
    # Close bot sessions
    await main_bot.session.close()
    await test_bot.session.close()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Setup startup and shutdown events
    app.add_event_handler("startup", on_startup)
    app.add_event_handler("shutdown", on_shutdown)
    
    # Run the FastAPI application with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
