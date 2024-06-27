from datetime import datetime
import json
from os import getenv
from typing import Type

from aiogram import Router, F, flags, html
from aiogram.types import Message
from aiogram.filters import MagicData

import redis

from utils.get_week_number import get_week_number
from utils.schedule_parser import Schedule

REDIS_URL = getenv("REDIS_URL")

r = redis.Redis.from_url(url=REDIS_URL)

router = Router()
router.message.filter(MagicData(F.user))


@router.message(F.text == "📅 Розклад")
@flags.show_main_menu
async def schedule_command_handler(message: Message, user: Type) -> None:
	now = datetime.now()
	day_of_week = datetime.weekday(now)
	if day_of_week > 5:
		await message.answer("Сьогодні вихідні")
		return
	start_date = json.loads(r.get("time_managment"))["FirstWeek"]
	current_week = get_week_number(datetime.strptime(start_date, '%d.%m.%Y'))

	schedule = Schedule(json.loads(r.get("schedule"))).get_schedule_data(user.group, current_week, current_week)

	EMOJI_NUMBERS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
	DAYS_OF_WEEK = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"]

	bells_data = json.loads(r.get("bells"))

	result = html.bold(f"🗓 Тиждень: {current_week}\n🕒 {DAYS_OF_WEEK[day_of_week]}\n\n")
	for pair in schedule:
		i = schedule.index(pair)
		p_result = f"{EMOJI_NUMBERS[i]} {html.bold(bells_data[i])}\n"
		for lesson in pair:
			p_result += f'{html.bold(lesson)}\n' if lesson.name else ''
		result += f"{p_result}\n"

	await message.answer(result)
