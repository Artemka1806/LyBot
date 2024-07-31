from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.fsm.storage.redis import RedisStorage


class ThrottlingMiddleware(BaseMiddleware):
	def __init__(self, storage: RedisStorage):
		self.storage = storage

	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any],
	) -> Any:
		if event.chat.type == "private":
			user = f"user{event.from_user.id}"

			check_user = await self.storage.redis.get(name=user)

			if check_user:
				if int(check_user.decode()) == 1:
					await self.storage.redis.set(name=user, value=0, ex=3)
					print("бля, я такий дебіл... закінчити прекрасне спілкування з прекрасною дівчиною... це поразка тотальна")
				return
			await self.storage.redis.set(name=user, value=1, ex=3)

		return await handler(event, data)
