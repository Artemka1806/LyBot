from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

import config


class Config():
	groups = config.GROUPS
	reserved_accounts = config.RESERVED_ACCOUNTS
	main_menu_buttons = config.MAIN_MENU_BUTTONS
	main_menu_size = config.MAIN_MENU_SIZE


class ExtraDataMiddleware(BaseMiddleware):
	async def __call__(
		self,
		handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: Dict[str, Any],
	) -> Any:
		data["config"] = Config
		return await handler(event, data)
