from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def keyboard(prefix: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Так", callback_data=f"{prefix}yes"),
        InlineKeyboardButton(text="❌ Hi", callback_data=f"{prefix}no")
    )

    return builder.as_markup()
