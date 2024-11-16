from datetime import datetime
from enum import Enum
import json
from os import getenv
from typing import Type
import pytz

from aiogram import Bot, Router, F, flags, html
from aiogram.types import Message, URLInputFile, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import MagicData, Command
from aiogram.filters.callback_data import CallbackData

import redis

from utils.get_week_number import get_week_number
from utils.schedule_parser import Schedule

REDIS_URL = getenv("REDIS_URL")

r = redis.Redis.from_url(url=REDIS_URL)

router = Router()
router.message.filter(F.chat.type == "private")
router.message.filter(MagicData(F.user))


class Action(Enum):
	ANSWER = 0
	EDIT = 1


class ScheduleTime(Enum):
	NOW = 0
	NEXT_DAY = 1


class ScheduleCallback(CallbackData, prefix="nodb_schedule"):
	group: str
	week: int
	day: int


async def answer_with_schedule(
	bot: Bot,
	message: Message,
	group: str,
	action: Action = Action.ANSWER,
	schedule_time: ScheduleTime = ScheduleTime.NOW,
	week: int = get_week_number(datetime.now().strptime(json.loads(r.get("time_managment"))["FirstWeek"], '%d.%m.%Y')),
	day: int = datetime.now(pytz.utc).astimezone(pytz.timezone('Europe/Kiev')).weekday(),
):
	try:
		next_day = day + 1
		next_week = week

		previous_day = day - 1
		previous_week = week

		if schedule_time == ScheduleTime.NOW:
			if day > 4:
				day = 0
				week = week + 1 if week < 3 else 0
				next_day = 1
				next_week = week

		if day == 4:
			next_day = 0
			if week == 3:
				next_week = 0
			else:
				next_week += 1
		elif day == 0:
			previous_day = 4
			if week == 0:
				previous_week = 3
			else:
				previous_week -= 1

		schedule = Schedule(json.loads(r.get("schedule"))).get_schedule_data(group, week, day)

		EMOJI_NUMBERS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
		DAYS_OF_WEEK = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"]

		bells_data = json.loads(r.get("bells"))

		result = html.bold(f"🗓 Тиждень: {week + 1}\n🕒 {DAYS_OF_WEEK[day]}\n\n")
		for pair in schedule:
			i = schedule.index(pair)
			p_result = f"{EMOJI_NUMBERS[i]} {html.bold(bells_data[i])}\n"
			for lesson in pair:
				p_result += f'{html.bold(lesson)}\n' if lesson.name else ''
			result += f"{p_result}\n"
		builder = InlineKeyboardBuilder()
		builder.button(text="◀️", callback_data=ScheduleCallback(group=group, week=previous_week, day=previous_day))
		builder.button(text="▶️", callback_data=ScheduleCallback(group=group, week=next_week, day=next_day))
		builder.button(text="⏪", callback_data=ScheduleCallback(group=group, week=week - 1 if week > 0 else 3, day=day))
		builder.button(text="⏩", callback_data=ScheduleCallback(group=group, week=week + 1 if week < 3 else 0, day=day))
		builder.button(text="Розклад на тиждень", callback_data=f"week_{week}_{day}")
		builder.adjust(2)

		if action == Action.EDIT:
			await bot.edit_message_text(result, chat_id=message.chat.id, message_id=message.message_id, reply_markup=builder.as_markup())
			return
		else:
			await message.answer(result, reply_markup=builder.as_markup())

		return

	except (KeyError, TypeError):
		await message.answer(f'{html.bold("Не вдалося знайти розклад для вашої групи")}\nСпробуйте змінити її в налаштуваннях')


@router.message(F.text == "📅 Розклад")
@flags.show_main_menu
async def schedule_handler(message: Message, user: Type, bot: Bot) -> None:
	await answer_with_schedule(bot, message, user.group)


@router.message(Command("schedule_t"))
@flags.show_main_menu
async def schedule_t_command_handler(message: Message, bot: Bot, user: Type) -> None:
	await answer_with_schedule(bot, message, user.group, day=4)


@router.callback_query(ScheduleCallback.filter())
async def schedule_callback_handler(callback: CallbackQuery, callback_data: ScheduleCallback, bot: Bot) -> None:
	await answer_with_schedule(
		bot,
		callback.message,
		callback_data.group,
		Action.EDIT,
		ScheduleTime.NEXT_DAY,
		callback_data.week,
		callback_data.day
	)


@router.callback_query(F.data.startswith("week_"))
async def week_schedule_callback_handler(callback: CallbackQuery, user: Type, bot: Bot) -> None:
	data = callback.data.split("_")
	week = int(data[1])
	day = int(data[2])

	builder = InlineKeyboardBuilder()
	builder.button(text="Так", callback_data=f"file_{week}")
	builder.button(text="Ні", callback_data=ScheduleCallback(group=user.group, week=week, day=day))
	builder.adjust(1)

	await bot.edit_message_text(
		f"Ви збираєтесь завантижити файл з розкладом на {week+1}-тиждень, продовжити?",
		chat_id=callback.message.chat.id,
		message_id=callback.message.message_id,
		reply_markup=builder.as_markup()
	)

	return


@router.callback_query(F.data.startswith("file_"))
async def download_callback_handler(callback: CallbackQuery, user: Type, bot: Bot) -> None:
	data = callback.data.split("_")
	week = int(data[1])

	await callback.answer("⌛ Секунду...")

	await bot.send_message(
		callback.message.chat.id,
		"нє"
	)
	return
