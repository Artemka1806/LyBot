from bson import ObjectId
from os import getenv
from typing import Type

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command, StateFilter, MagicData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv

from models.user import User
from keyboards import group_select, main_menu, login

load_dotenv()

SENDER_EMAIL = getenv("SENDER_EMAIL")
SENDER_PASSWORD = getenv("SENDER_PASSWORD")


router = Router()
router.message.filter(F.chat.type == "private")
router.message.filter(MagicData(~F.user))


class UserLogin(StatesGroup):
    entering_group = State()


@router.message(CommandStart())
async def start_command_handler(message: Message, command: CommandObject, state: FSMContext) -> None:
    if command.args:
        await state.update_data(mongo_id=command.args)
        await message.answer("Успішно!\nВиберіть свою групу:", reply_markup=group_select.keyboard)
        await state.set_state(UserLogin.entering_group)
    else:
        await message.answer("Будь ласка, увійдіть за допомогою кнопки нижче:", reply_markup=login.keyboard)


@router.message(UserLogin.entering_group, F.text.regexp(r"^(1[0-2])-([А-Я])$"))
async def group_entered(message: Message, state: FSMContext, config: Type) -> None:
    if message.text not in config.groups:
        await message.answer("Введіть правильну групу: ", reply_markup=group_select.keyboard)
        return

    user_data = await state.get_data()
    user = await User.find_one({"id": ObjectId(user_data["mongo_id"])})
    if not user:
        await state.clear()
        await message.answer("Невірний користувач, спробуйте ще раз")
        return

    user.tg_id = message.from_user.id
    user.group = message.text
    user.name = message.from_user.first_name
    user.username = message.from_user.username

    await user.commit()
    await state.clear()

    await message.answer("Успішно! Використовуйте головне меню:", reply_markup=main_menu.keyboard(user))


@router.message(Command("cancel"))
async def clearstate_command_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Успішно!")


@router.message(StateFilter(None))
async def login_required(message: Message) -> None:
    if not message.from_user.is_bot:
        await message.answer("Будь ласка, увійдіть за допомогою кнопки нижче:", reply_markup=login.keyboard)
