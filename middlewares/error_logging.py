from os import getenv
import traceback

from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from dotenv import load_dotenv

load_dotenv()

ERROR_LOG_CHAT_ID = getenv("ERROR_LOG_CHAT_ID")


class ErrorLoggingMiddleware(BaseMiddleware):
	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any],
	) -> Any:
		bot = data["bot"]
		try:
			return await handler(event, data)
		except Exception:
			d = traceback.format_exc()
			print(d)
			await bot.send_message(ERROR_LOG_CHAT_ID, f"User: {data['user'].to_mongo()}")
			await bot.send_message(ERROR_LOG_CHAT_ID, d)
