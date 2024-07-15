from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

builder = ReplyKeyboardBuilder()

builder.add(KeyboardButton(text="❌ Скасувати"))

builder.adjust(1)

keyboard = builder.as_markup(
	resize_keyboard=True,
	input_field_placeholder="Виберіть дію"
)
