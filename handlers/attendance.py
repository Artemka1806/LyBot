from aiogram import Bot, Router, F
from aiogram.filters import Command, StateFilter, MagicData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from typing import Type

from keyboards import attendance_status_select as ass
from keyboards import main_menu

router = Router()
router.message.filter(MagicData(F.user))


class UserStatus(StatesGroup):
	sets_status = State()


@router.message(F.text == "🚗 Відвідування")
async def attendance_command_handler(message: Message, state: FSMContext, user: Type) -> None:
	await message.answer(f'Ваш статус - "{ass.ANSWER_OPTIONS[int(user.status)]}".\nВиберіть статус:', reply_markup=ass.keyboard)
	await state.set_state(UserStatus.sets_status)


@router.message(UserStatus.sets_status)
async def status_selected(message: Message, state: FSMContext, user: Type) -> None:
	if message.text not in ass.ANSWER_OPTIONS:
		await message.answer("Невірний статус", reply_markup=ass.keyboard)
		return

	user.status = ass.ANSWER_OPTIONS.index(message.text)
	user.save()

	await message.answer(f'Успішно оновлено статус на "{message.text}"', reply_markup=main_menu(user))
