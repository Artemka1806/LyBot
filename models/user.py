import datetime

from umongo import Document, fields

from .common import instance


@instance.register
class User(Document):
	tg_id = fields.IntegerField(unique=True)
	name = fields.StringField(max_length=64)
	username = fields.StringField(max_length=32)
	given_name = fields.StringField()
	family_name = fields.StringField()
	email = fields.EmailField(required=True, unique=True)
	avatar_url = fields.StringField()
	group = fields.StringField(max_length=4)
	role = fields.IntField(default=0)
	status = fields.IntegerField(min_value=0, max_value=3, default=3)
	created_at = fields.DateTimeField(default=datetime.datetime.utcnow)
