from datetime import datetime, timedelta, timezone


def get_week_number(start_date: datetime):
	current_date = datetime.now(tz=timezone(timedelta(hours=3)))
	data = current_date
	current_date = datetime(data.year, data.month, data.day)
	delta = current_date - start_date

	weeks = delta.days / 7
	return int(weeks % 4) + 1
