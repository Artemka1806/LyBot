from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

ANSWER_OPTIONS = [
	"✉️ Змінити пошту", "👥 Змінити групу",
	"🔑 Вийти з акаунту", "📝 Ліцензії"
]

builder = ReplyKeyboardBuilder()

for answer in ANSWER_OPTIONS:
	builder.add(KeyboardButton(text=answer))

builder.add(KeyboardButton(text="❌ Скасувати"))

builder.adjust(2)

keyboard = builder.as_markup(
	resize_keyboard=True,
	input_field_placeholder="Виберіть дію"
)
