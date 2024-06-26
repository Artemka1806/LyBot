from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

ANSWER_OPTIONS = [
	"✅ Прибув", "🚗 В дорозі",
	"🕘 Запізнюся", "🏠 Дома"
]

builder = ReplyKeyboardBuilder()

for answer in ANSWER_OPTIONS:
	builder.add(KeyboardButton(text=answer))

builder.adjust(2)

keyboard = builder.as_markup(
	resize_keyboard=True,
	input_field_placeholder="Виберіть статус"
)
