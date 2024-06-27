from email.mime.text import MIMEText
from os import getenv
import random
import smtplib
from typing import Type

from aiogram import Bot, Router, F
from aiogram.filters import Command, StateFilter, MagicData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv

from models.user import User
from keyboards import group_select, main_menu

load_dotenv()

SENDER_EMAIL = getenv("SENDER_EMAIL")
SENDER_PASSWORD = getenv("SENDER_PASSWORD")


router = Router()
router.message.filter(MagicData(~F.user))


class UserLogin(StatesGroup):
    entering_email = State()
    entering_code = State()
    entering_group = State()


@router.message(Command("login"))
async def login_command_handler(message: Message, state: FSMContext) -> None:
    await message.answer("Введіть ліцейну електронну пошту:")
    await state.set_state(UserLogin.entering_email)


@router.message(UserLogin.entering_email, (F.text.endswith("ztu.edu.ua")) | (F.text.endswith("example.com")))
async def email_entered(message: Message, state: FSMContext, bot: Bot, config: Type) -> None:
    if message.text in config.reserved_accounts.keys():
        await state.update_data(email=message.text.lower(), code=config.reserved_accounts[message.text.lower()])
        await state.set_state(UserLogin.entering_code)
        await message.answer("Введіть код доступу до зарезервованого акаунту:")
        return

    await bot.send_chat_action(message.chat.id, "typing")

    await state.update_data(email=message.text.lower())
    user_data = await state.get_data()
    random_number = random.randint(1000, 9999)
    await state.update_data(code=random_number)

    msg = MIMEText(str(random_number))
    msg["Subject"] = "Код доступу"
    msg["From"] = SENDER_EMAIL
    msg["To"] = user_data["email"]
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp_server.sendmail(SENDER_EMAIL, user_data["email"], msg.as_string())

    await message.answer(f"На пошту {user_data['email']} відправлено код підтвердження. Ведіть його:")
    await state.set_state(UserLogin.entering_code)


@router.message(UserLogin.entering_code)
async def code_entered(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    if str(user_data["code"]) == message.text:
        await message.answer("Успішно!\nВиберіть свою групу:", reply_markup=group_select.keyboard)
        await state.set_state(UserLogin.entering_group)
    else:
        await message.answer("Невірний код!")


@router.message(UserLogin.entering_group, F.text.regexp(r"^(1[0-2])-([А-Я])$"))
async def group_entered(message: Message, state: FSMContext, config: Type) -> None:
    if message.text not in config.groups:
        await message.answer("Введіть правильну групу: ", reply_markup=group_select.keyboard)
        return
    await state.update_data(group=message.text)
    user_data = await state.get_data()
    await state.clear()

    user = User(
        tg_id=message.from_user.id,
        name=message.from_user.first_name,
        username=message.from_user.username,
    )
    try:
        user.email = user_data["email"]
        user.group = user_data["group"]
    except KeyError:
        await message.answer("Було втрачено певну частину введених вами даних. Пройдіть процес авторизації заново за допомогою /login")
        return

    user.save()

    await message.answer("Успішно! Використовуйте головне меню:", reply_markup=main_menu.keyboard(user))


@router.message(UserLogin.entering_email, (F.text.contains("@")) & (F.text.contains(".")))
async def wrong_email_handler(message: Message) -> None:
    await message.answer("Схоже, що ви вводите адресу стороннього поштового сервісу. Наразі підтримуються тільки пошти домену ztu.edu.ua")


@router.message(Command("cancel"))
async def clearstate_command_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Успішно!")


@router.message(StateFilter(None))
async def login_required(message: Message) -> None:
    await message.answer("Будь ласка, увійдіть за допомогою /login")
