from asyncio import sleep
from math import inf

from aiogram import Router, Bot, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters.chat_member_updated import \
	ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from cachetools import TTLCache

from models.group import Group

router = Router()
migration_cache = TTLCache(maxsize=inf, ttl=10.0)


@router.message(F.migrate_from_chat_id)
async def group_to_supegroup_migration(message: Message, bot: Bot):
	group = await Group.find_one({"tg_id": message.migrate_from_chat_id})
	if group:
		group.tg_id = message.chat.id
	else:
		group = Group(
			tg_id=message.chat.id,
			name=message.chat.title,
		)

	await group.commit()

	await message.answer(
		"Група щойно мігрувала в супергрупу. Але, не переживайте, я вже обробив цю \"велику\" подію. Все під контролем 😎 "
	)
	migration_cache[message.chat.id] = True


@router.my_chat_member(
	ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION),
	F.chat.type.in_({"group", "supergroup"})
)
async def bot_added_to_group(event: ChatMemberUpdated, bot: Bot):
	await sleep(1.0)
	if event.chat.id not in migration_cache.keys():
		group = await Group.find_one({"tg_id": event.chat.id})
		if not group:
			group = Group(
				tg_id=event.chat.id,
				name=event.chat.title,
			)
			await group.commit()

		await event.answer("👋")


@router.my_chat_member(
	ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION),
	F.chat.type.in_({"group", "supergroup"})
)
async def bot_left_group(event: ChatMemberUpdated, bot: Bot):
	group = await Group.find_one({"tg_id": event.chat.id})
	if group:
		await group.delete()


@router.message(F.new_chat_member, ~F.new_chat_member.is_bot, F.chat.id.in_({-1001904185128, -4283931949}))
async def new_member(message: Message):
	await message.reply("+ раб 🤑")
