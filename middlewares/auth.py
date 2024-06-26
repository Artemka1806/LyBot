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
		users = User.objects(tg_id=event.message.from_user.id)
		if users:
			data["user"] = users.first()
		else:
			data["user"] = None

		return await handler(event, data)
