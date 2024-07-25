import datetime
from enum import Enum

from mongoengine import *


class Role(Enum):
	USER = 0
	MANAGER = 1
	ADMIN = 2


class User(Document):
	tg_id = DecimalField(unique=True, required=True)
	name = StringField(max_length=64, required=True)
	username = StringField(max_length=32)
	email = EmailField(required=True)
	group = StringField(max_length=4, required=True)
	role = EnumField(Role, default=Role.USER)
	status = DecimalField(min_value=0, max_value=3, default=3)
	created_at = DateTimeField(default=datetime.datetime.utcnow)
