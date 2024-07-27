import datetime

from umongo import Document, fields

from .common import instance


@instance.register
class User(Document):
	tg_id = fields.IntegerField(unique=True, required=True)
	name = fields.StringField(max_length=64, required=True)
	username = fields.StringField(max_length=32)
	email = fields.EmailField(required=True)
	group = fields.StringField(max_length=4, required=True)
	role = fields.IntField(default=0)
	status = fields.IntegerField(min_value=0, max_value=3, default=3)
	created_at = fields.DateTimeField(default=datetime.datetime.utcnow)
