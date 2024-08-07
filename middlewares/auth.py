from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from models.user import User


class AuthMiddleware(BaseMiddleware):
	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any],
	) -> Any:
		if event.callback_query and event.callback_query.data.startswith("nodb_"):
			return await handler(event, data)
		tg_id = 0
		if event.callback_query:
			tg_id = event.callback_query.from_user.id
		elif event.message:
			tg_id = event.message.from_user.id
		elif event.pre_checkout_query:
			tg_id = event.pre_checkout_query.from_user.id
		else:
			return await handler(event, data)

		data["user"] = await User.find_one({"tg_id": tg_id})

		return await handler(event, data)
