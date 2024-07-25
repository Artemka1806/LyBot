from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

MENU_OPTIONS = [
	"Надіслати групам"
]

builder = ReplyKeyboardBuilder()

for menu in MENU_OPTIONS:
	builder.add(KeyboardButton(text=menu))

builder.add(KeyboardButton(text="❌ Скасувати"))

builder.adjust(2)

keyboard = builder.as_markup(
	resize_keyboard=True,
	input_field_placeholder="Виберіть дію"
)
