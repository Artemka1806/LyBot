from enum import Enum
from typing import Type

from aiogram import Bot, Router, F, flags, html
from aiogram.types import Message, URLInputFile, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter, MagicData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from aiogram_album import AlbumMessage

from keyboards import admin_menu, cancel


router = Router()
router.message.filter(F.chat.type == "private")
router.message.filter(MagicData(F.user.role.MANAGER | F.user.role.ADMIN))


class AdminSendMessageAction(StatesGroup):
	entering_message = State()
	choosing_recipient = State()


@router.message(F.text == "😎 Адміністрування", )
async def admin_handler(message: Message) -> None:
	await message.answer("Виберіть дію:", reply_markup=admin_menu.keyboard)


@router.message(F.text == "❌ Скасувати")
@flags.show_main_menu
async def cancel_handler(message: Message, state: FSMContext) -> None:
	await message.answer("ОК")
	await state.clear()


@router.message(F.text == "Надіслати групам")
async def send_to_groups_handler(message: Message, state: FSMContext) -> None:
	await message.answer("Введіть ваше повідомлення", reply_markup=cancel.keyboard)
	await state.set_state(AdminSendMessageAction.entering_message)


@router.message(F.media_group_id, AdminSendMessageAction.entering_message)
async def entered_album_handler(message: AlbumMessage, state: FSMContext) -> None:
	# await state.update_data(messages=message.message_ids)
	# await state.set_state(AdminSendMessageAction.choosing_recipient)
	# await message.answer("Тепер введіть ID чату")
	await message.answer("Альбоми (кілька фотографій в одному повідомлення) наразі не підтримуються")


@router.message(AdminSendMessageAction.entering_message)
async def entered_message_handler(message: Message, state: FSMContext) -> None:
	await state.update_data(messages=[message.message_id])
	await state.set_state(AdminSendMessageAction.choosing_recipient)
	await message.answer("Тепер введіть ID чату")


@router.message(AdminSendMessageAction.choosing_recipient)
async def choosed_recipient_handler(message: Message, state: FSMContext, bot: Bot) -> None:
	data = await state.get_data()
	message_ids = data["messages"]
	message_ids.sort()
	print("id:", message.text)
	await bot.copy_messages(chat_id=message.text, from_chat_id=message.chat.id, message_ids=message_ids)
	await message.answer("Успішно!", reply_markup=admin_menu.keyboard)
	await state.clear()
