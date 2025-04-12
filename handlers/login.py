from bson import ObjectId
from os import getenv
from typing import Type, Optional, Dict, Any
import json

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command, StateFilter, MagicData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
from ldap3 import Server, Connection, ALL
from marshmallow.exceptions import ValidationError
from pymongo.errors import DuplicateKeyError

from models.user import User
from keyboards import group_select, main_menu, login

load_dotenv()

LDAP_SERVER = getenv("LDAP_SERVER")
LDAP_PORT = int(getenv("LDAP_PORT"))
LDAP_BIND_DN = getenv("LDAP_BIND_DN")
LDAP_BASE_DN = getenv("LDAP_BASE_DN")

router = Router()
router.message.filter(F.chat.type == "private")


class UserLogin(StatesGroup):
    entering_login = State()
    entering_password = State()
    entering_group = State()


@router.message(CommandStart(), MagicData(~F.user))
async def start_command_handler(message: Message, command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(UserLogin.entering_login)
    await message.answer("Будь ласка, введіть логін:")


@router.message(UserLogin.entering_login, MagicData(~F.user))
async def login_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(login=message.text)
    await state.set_state(UserLogin.entering_password)
    await message.answer("Введіть пароль:")


async def authenticate_ldap(login: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with LDAP and return user attributes if successful"""
    try:
        server = Server(LDAP_SERVER, port=LDAP_PORT, get_info=ALL)
        bind_dn = f'{login}@{LDAP_BIND_DN}'
        
        conn = Connection(server, bind_dn, password, auto_bind=True)
        search_filter = f'(sAMAccountName={login})'
        
        conn.search(LDAP_BASE_DN, search_filter, attributes=['*'])
        
        if not conn.entries:
            conn.unbind()
            return None
            
        entry = conn.entries[0]
        try:
            decoded_entry = json.loads(entry.entry_to_json())
            attrs = decoded_entry.get('attributes', {})
            
            user_data = {
                'name': attrs.get('name', [''])[0],
                'email': attrs.get('mail', [''])[0]
            }
            
            conn.unbind()
            return user_data
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            conn.unbind()
            return None
            
    except Exception:
        return None


@router.message(UserLogin.entering_password, MagicData(~F.user))
async def password_entered(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    login = data["login"]
    password = message.text

    user_data = await authenticate_ldap(login, password)
    
    if user_data:
        name = user_data['name']
        email = user_data['email']
        
        if not email:
            await message.answer("❌ Помилка: відсутня електронна пошта. Зверніться до адміністратора.")
            return
            
        await User.ensure_indexes()
        
        # Спочатку перевіряємо, чи існує користувач з такою email
        user = await User.find_one({"email": email})
        
        if user:
            # Оновлюємо існуючого користувача
            user.tg_id = message.from_user.id
            user.ztu_name = name
        else:
            # Створюємо нового користувача
            try:
                user = User(
                    tg_id=message.from_user.id,
                    ztu_name=name,
                    email=email,
                )
            except ValidationError:
                await message.answer("❌ Помилка валідації даних. Спробуйте ще раз /start")
                return
                
        try:
            await user.commit()
            await state.set_state(UserLogin.entering_group)
            await message.answer("Успішно!\nВиберіть свою групу:", reply_markup=group_select.keyboard)
        except Exception as e:
            await message.answer(f"❌ Помилка при збереженні даних: {str(e)}. Спробуйте ще раз /start")
    else:
        await message.answer("❌ Невірний логін або пароль. Спробуйте ще раз /start")


@router.message(UserLogin.entering_group)
async def group_entered(message: Message, state: FSMContext, user: User) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Виберіть групу:", reply_markup=group_select.keyboard)
        return

    if not user:
        await state.clear()
        await message.answer("Невірний користувач, спробуйте ще раз /start")
        return

    user.group = message.text
    await user.commit()
    await state.clear()

    await message.answer("Успішно! Використовуйте головне меню:", reply_markup=main_menu.keyboard(user))


@router.message(Command("cancel"))
async def clearstate_command_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Успішно!")


@router.message()
async def login_required(message: Message) -> None:
    if not message.from_user.is_bot:
        await message.answer("Будь ласка, увійдіть заново /start")
