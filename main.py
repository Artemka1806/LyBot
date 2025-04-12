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
from contextlib import asynccontextmanager

from middlewares import *
from handlers import ROUTERS
from models.common import instance
from models.user import User
from keyboards import main_menu
from middlewares.throttlinig import ThrottlingMiddleware
from utils.change_users_status import change_users_status
from utils.bulk_mailing import bulk_mailing
# Import the API router
from routers.api import router as api_router, init_redis as init_api_redis

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
# Initialize Redis client in API router
init_api_redis(r)

# Bot initialization
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


# FastAPI app initialization
@asynccontextmanager
async def lifespan_context(app: FastAPI):
    # Set up webhooks for bot
    await bot.set_webhook(url=WEBHOOK_URL)
    logging.info(f"Webhook set successfully to {WEBHOOK_URL}")

    # Set up schedulers
    if getenv("DISABLE_SCHEDULER") is None:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.configure(timezone="Europe/Kyiv")
        scheduler.add_job(save_api_data, 'interval', minutes=5)
        scheduler.add_job(change_users_status, "cron", hour=20, minute=0)
        scheduler.add_job(send_reminder, "cron", hour=8, minute=5)
        scheduler.start()
    
    yield  # App runs here
    
    # Shutdown code (previously in on_shutdown)
    await bot.session.close()

# Update FastAPI app initialization to use the lifespan
app = FastAPI(lifespan=lifespan_context)

# Configure CORS for API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router)

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


# Telegram webhook handlers
@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    """Handle webhook updates for main bot"""
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)
    return {"ok": True}


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Run the FastAPI application with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
