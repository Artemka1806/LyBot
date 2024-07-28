from asyncio import sleep
from enum import Enum
from typing import List, Type

from aiogram import Bot, Router, F, flags, html
from aiogram.types import Message, URLInputFile, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter, MagicData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from aiogram_album import AlbumMessage

from keyboards import admin_menu, cancel, main_menu
from models.group import Group


router = Router()
router.message.filter(F.chat.type == "private")
router.message.filter(MagicData(F.user.role > 0))


class GroupSelectCallback(CallbackData, prefix="group_select"):
	tg_id: int
	selected: bool


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
	group_cursor = Group.find()
	groups = []
	builder = InlineKeyboardBuilder()
	async for group in group_cursor:
		groups.append({"tg_id": group.tg_id, "name": group.name, "selected": True})
		builder.button(text=f"✅ {group.name}", callback_data=GroupSelectCallback(tg_id=group.tg_id, selected=True))
	builder.row(InlineKeyboardButton(text="🌼 Відправити", callback_data="send_to_groups"))
	builder.adjust(2)
	await state.update_data(groups=groups)

	await message.answer("Тепер виберіть чат", reply_markup=builder.as_markup())
	await state.set_state(AdminSendMessageAction.choosing_recipient)


@router.callback_query(GroupSelectCallback.filter(), AdminSendMessageAction.choosing_recipient)
async def select_recipient_handler(callback: CallbackQuery, callback_data: GroupSelectCallback, state: FSMContext) -> None:
	data = await state.get_data()
	groups = data["groups"]

	builder = InlineKeyboardBuilder()
	for group in groups:
		if callback_data.tg_id == group["tg_id"]:
			group["selected"] = False if callback_data.selected else True
		emoji = "✅" if group["selected"] else "❌"
		builder.button(text=f"{emoji} {group['name']}", callback_data=GroupSelectCallback(tg_id=group["tg_id"], selected=group["selected"]))
	builder.row(InlineKeyboardButton(text="🌼 Відправити", callback_data="send_to_groups"))
	builder.adjust(2)
	await state.update_data(groups=groups)

	await callback.message.edit_reply_markup(reply_markup=builder.as_markup())


async def mass_send(admin_id: int, chat_ids: List[str] | List[int], from_chat_id: int | str, message_ids: List[int], bot: Bot):
	if chat_ids and message_ids:
		message_ids.sort()
		for chat_id in chat_ids:
			await bot.copy_messages(chat_id=chat_id, from_chat_id=from_chat_id, message_ids=message_ids)
			await sleep(2)
	await bot.send_message(admin_id, "Успішно закінчено розсилку")


@router.callback_query(F.data == "send_to_groups", AdminSendMessageAction.choosing_recipient)
async def send_query_handler(callback: CallbackQuery, state: FSMContext, bot: Bot, user: Type) -> None:
	data = await state.get_data()
	groups = data["groups"]
	groups_to_send = []
	for group in groups:
		if group["selected"]:
			groups_to_send.append(group["tg_id"])
	await callback.answer("Розсилка почалась!")
	await bot.send_message(callback.from_user.id, "Головне меню", reply_markup=main_menu.keyboard(user))
	await state.clear()
	await mass_send(callback.from_user.id, groups_to_send, callback.message.chat.id, data["messages"], bot)
