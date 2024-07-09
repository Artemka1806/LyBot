from datetime import datetime


def get_week_number(start_date: datetime):
	current_date = datetime.now()
	delta = current_date - start_date
	weeks = delta.days / 7
	return int(weeks % 4)
