from datetime import datetime
import pytz

def get_week_number(start_date: datetime):
    kyiv_tz = pytz.timezone('Europe/Kiev')
    if start_date.tzinfo is None:
        start_date = kyiv_tz.localize(start_date)
    current_date = datetime.now(kyiv_tz)
    delta = current_date - start_date
    weeks = delta.days // 7
    return weeks % 4
