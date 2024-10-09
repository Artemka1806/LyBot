from os import getenv

from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

AD_IMAGE_URL = getenv("AD_IMAGE_URL")
AD_URL = getenv("AD_URL")

AD_WORDS = ["🚗 Відвідування"]


class AdMiddleware(BaseMiddleware):
	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any],
	) -> Any:

		# if event.text in AD_WORDS:
		# 	bot = data["bot"]
		# 	builder = InlineKeyboardBuilder()
		# 	builder.row(
		# 		InlineKeyboardButton(text="Дізнатися більше", url=AD_URL)
		# 	)
		# 	try:
		# 		await bot.send_photo(chat_id=event.chat.id, photo=AD_IMAGE_URL, reply_markup=builder.as_markup())
		# 	except Exception as e:
		# 		print(e)

		return await handler(event, data)
