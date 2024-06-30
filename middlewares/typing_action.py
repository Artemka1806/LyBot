from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.utils.chat_action import ChatActionSender


class TypingActionMiddleware(BaseMiddleware):
	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any],
	) -> Any:
		if event.callback_query:
			return await handler(event, data)

		async with ChatActionSender(
			action="typing",
			chat_id=event.message.chat.id,
			bot=data["bot"]
		):
			return await handler(event, data)
