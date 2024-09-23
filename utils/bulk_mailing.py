import asyncio
from aiogram import Bot
from models.user import User

async def bulk_mailing(bot: Bot, text: str, error_group: int) -> None:
    async for user in User.find():
        try:
            await bot.send_message(user.tg_id, text)
        except Exception as e:
            await bot.send_message(int(error_group), str(e))
        await asyncio.sleep(0.3)
