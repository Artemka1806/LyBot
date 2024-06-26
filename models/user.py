import datetime

from mongoengine import *


class User(Document):
	tg_id = DecimalField(unique=True, required=True)
	name = StringField(max_length=64, required=True)
	username = StringField(max_length=32)
	email = EmailField(required=True)
	group = StringField(max_length=4, required=True)
	role = DecimalField(min_value=0, max_value=2, default=0)
	status = DecimalField(min_value=0, max_value=3, default=3)
	created_at = DateTimeField(default=datetime.datetime.utcnow)
