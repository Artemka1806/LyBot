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
		tg_id = 0
		if event.callback_query:
			tg_id = event.callback_query.from_user.id
		elif event.message:
			tg_id = event.message.from_user.id
		elif event.pre_checkout_query:
			tg_id = event.pre_checkout_query.from_user.id
		else:
			return await handler(event, data)
		users = User.objects(tg_id=tg_id)
		if users:
			data["user"] = users.first()
		else:
			data["user"] = None

		return await handler(event, data)
