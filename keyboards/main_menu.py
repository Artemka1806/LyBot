from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import config


def keyboard(user):
	builder = ReplyKeyboardBuilder()

	for button in config.MAIN_MENU_BUTTONS:
		builder.add(KeyboardButton(text=button))

	if user.role.MANAGER or user.role.ADMIN:
		builder.add(KeyboardButton(text="😎 Адміністрування"))

	builder.adjust(config.MAIN_MENU_SIZE)

	return builder.as_markup(
		resize_keyboard=True,
		input_field_placeholder="Виберіть дію"
	)
