from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

builder = InlineKeyboardBuilder()
builder.row(
    InlineKeyboardButton(text="Увійти за допомогою Google", url="https://lybotapi.onrender.com/tgbotlogin"),
)

keyboard = builder.as_markup()
