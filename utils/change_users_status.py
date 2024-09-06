from models.user import User

async def change_users_status() -> None:
    async for user in User.find():
        user.status = 3
        await user.commit()
