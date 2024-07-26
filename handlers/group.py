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
	groups = Group.objects(tg_id=message.chat.id)
	if groups:
		group = groups.first()
		group["tg_id"] = message.chat.id
		group.save()
	else:
		group = Group(
			tg_id=message.chat.id,
			name=message.chat.title,
		)
		group.save()

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
		groups = Group.objects(tg_id=event.chat.id)
		if not groups:
			group = Group(
				tg_id=event.chat.id,
				name=event.chat.title,
			)
			group.save()

		await event.answer("A placeholder. I will replace it later.")


@router.my_chat_member(
	ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION),
	F.chat.type.in_({"group", "supergroup"})
)
async def bot_left_group(event: ChatMemberUpdated, bot: Bot):
	groups = Group.objects(tg_id=event.chat.id)
	if groups:
		groups.first().delete()
