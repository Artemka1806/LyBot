from aiogram import html, flags, F, Router
from aiogram.filters import CommandStart, Command, MagicData
from aiogram.types import Message

from keyboards import main_menu

# Create a router for commands
router = Router()


@router.message(CommandStart(), MagicData(F.user))
async def start_command_handler(message: Message, user: type) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!", reply_markup=main_menu.keyboard(user))


@router.message(Command("waltz"))
@flags.show_main_menu
async def waltz_command_handler(message: Message) -> None:
    await message.answer("""Bring out the charge of the love brigade
There is spring in the air once again
Drink to the sound of the song parade
There is music and love everywhere
Give a little love to me (I want it)
Take a little love from me
I wanna share it with you
I feel like a millionaire""")


@router.message(Command("error"))
@flags.show_main_menu
async def error_command_handler(message: Message) -> None:
    raise Exception("Love Of My Life\nhttps://youtu.be/sUJkCXE4sAA")


@router.message(Command("phid"), F.photo)
@flags.show_main_menu
async def get_photo_id_handler(message: Message) -> None:
    await message.answer(f"{message.photo[-1].file_id}")


@router.message(Command("copy"))
@flags.show_main_menu
async def copy_message_handler(message: Message) -> None:
    # Check if the message is a reply
    if not message.reply_to_message:
        await message.answer("Ця команда має бути відповіддю на повідомлення.")
        return
    
    # Get the chat ID from the command arguments
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Використання: /copy chat_id")
        return
    
    try:
        chat_id = int(args[1])
    except ValueError:
        await message.answer("Невірний ID чату. Будь ласка, вкажіть правильний числовий ID.")
        return
    
    try:
        # Copy the message to the specified chat
        await message.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id
        )
        await message.answer(f"Повідомлення скопійовано в чат {chat_id}")
    except Exception as e:
        await message.answer(f"Помилка: {str(e)}")