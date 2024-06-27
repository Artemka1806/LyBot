from config import GROUPS

DAYS_OF_WEEK = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]


class Lesson():
	def __init__(self, data: list):
		self.number = data[0]
		self.name = data[1]
		self.teacher = data[2]
		self.classroom = data[3]
		self.subgroup = data[4]

	def __str__(self):
		if self.number == "" and self.name == "" and self.teacher == "" and self.classroom == "" and self.subgroup == "":
			return ""
		return f"🔸{self.name}{f', {self.subgroup}гр.' if self.subgroup else  ''}\n{self.teacher}, каб. {self.classroom}"


class Schedule():
	def __init__(self, schedule_data: list) -> None:
		self.pure_data = schedule_data

	def get_schedule_data(self, group: str, week: int, day: int) -> list:
		if group not in GROUPS:
			return None
		result = []
		data = self.pure_data[GROUPS.index(group)][1][week][1][day][1]
		for pair in data:
			p = []
			for lesson in pair:
				p.append(Lesson(lesson))
			result.append(p)
		return result
