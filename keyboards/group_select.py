from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import config

builder = ReplyKeyboardBuilder()

for group in config.GROUPS:
	builder.add(KeyboardButton(text=group))

builder.adjust(5)

keyboard = builder.as_markup(
	resize_keyboard=True,
	input_field_placeholder="Виберіть групу"
)
