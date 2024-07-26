import datetime

from mongoengine import *


class Group(Document):
	tg_id = DecimalField(unique=True, required=True)
	name = StringField(max_length=64, required=True)
	group = StringField(max_length=4)
	added_at = DateTimeField(default=datetime.datetime.utcnow)
