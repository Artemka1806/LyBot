from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.dispatcher.flags import get_flag

from keyboards.main_menu import keyboard


class MenuMiddleware(BaseMiddleware):
	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any],
	) -> Any:
		show_main_menu = get_flag(data, "show_main_menu")
		if not show_main_menu or not data["user"]:
			return await handler(event, data)

		result = await handler(event, data)
		await event.answer("Головне меню", reply_markup=keyboard(data["user"]))
		return result
