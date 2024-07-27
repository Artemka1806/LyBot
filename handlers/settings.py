from typing import Type

from aiogram import Router, F, flags, html, Bot
from aiogram.filters import MagicData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards import settings_menu, cancel, inline_yes_no

router = Router()
router.message.filter(F.chat.type == "private")
router.message.filter(MagicData(F.user))


class UserSettings(StatesGroup):
	selecting_now = State()
	changing_now = State()


@router.message(F.text == "⚙️ Налаштування")
async def settings_handler(message: Message, state: FSMContext, user: Type) -> None:
	await message.answer(f'{html.bold("Налаштування")}\nІм\'я: {user.name}\nПошта: {html.spoiler(user.email)}\nГрупа: {user.group}', reply_markup=settings_menu.keyboard)
	await state.set_state(UserSettings.selecting_now)


@router.message(F.text == "📝 Ліцензії")
async def legal_handler(message: Message) -> None:
	await message.answer("TODO")


@router.message(F.text == "🔑 Вийти з акаунту")
async def logout_handler(message: Message) -> None:
	await message.answer("Ви дійсно хочете вийти з акаунту? Всі ваші дані будуть видалені", reply_markup=inline_yes_no.keyboard("logout:"))


@router.callback_query(F.data == "logout:yes")
async def logout(callback: CallbackQuery, user: Type, bot: Bot):
	await user.delete()
	await callback.message.delete()
	await callback.answer("Успішно!")
	await callback.message.answer("Будь ласка, увійдіть за допомогою /login")


@router.callback_query(F.data == "logout:no")
@flags.show_main_menu
async def logout_cancel(callback: CallbackQuery, bot: Bot):
	await callback.message.delete()
	await callback.answer("OK", show_alert=True)


@router.message(F.text == "❌ Скасувати")
@flags.show_main_menu
async def cancel_handler(message: Message, state: FSMContext) -> None:
	await state.clear()
	await message.answer("OK")


@router.message(UserSettings.selecting_now)
async def setting_selected(message: Message, state: FSMContext, user: Type) -> None:
	if message.text not in settings_menu.ANSWER_OPTIONS:
		return await message.answer("Невірна дія", reply_markup=settings_menu.keyboard)

	await state.set_state(UserSettings.changing_now)

	selected_setting = settings_menu.ANSWER_OPTIONS.index(message.text)
	await state.update_data(selected_setting=selected_setting)

	msg = ""
	if selected_setting == 0:
		msg = "Введіть нову пошту:"
	elif selected_setting == 1:
		msg = "Введіть вашу групу у фроматі 1Х-Х (наприклад: \"10-Б\")"
	else:
		return await message.answer("Невірна дія", reply_markup=settings_menu.keyboard)

	await message.answer(msg, reply_markup=cancel.keyboard)


@router.message(UserSettings.changing_now, (F.text.regexp(r"^(1[0-2])-([А-Я])$") | F.text.endswith("ztu.edu.ua")))
@flags.show_main_menu
async def setting_changed(message: Message, state: FSMContext, user: Type) -> None:
	try:
		user_data = await state.get_data()
		selected_setting = user_data["selected_setting"]

		if selected_setting == 0:
			user.email = message.text
		elif selected_setting == 1:
			user.group = message.text

		await user.commit()

		await message.answer(f"Успішно змінено налаштування!")
		await state.clear()
	except Exception:
		await message.answer(f"Помилка валідації!")
