import datetime

from umongo import Document, fields

from .common import instance


@instance.register
class User(Document):
	tg_id = fields.IntegerField(unique=True)
	name = fields.StringField(max_length=64)
	ztu_name = fields.StringField(allow_none=True)
	username = fields.StringField(max_length=32, allow_none=True)
	given_name = fields.StringField(allow_none=True)
	family_name = fields.StringField(allow_none=True)
	email = fields.EmailField(required=True, unique=True)
	avatar_url = fields.StringField(allow_none=True)
	group = fields.StringField(max_length=4)
	role = fields.IntField(default=0)
	status = fields.IntegerField(min_value=0, max_value=3, default=3)
	status_updated_at = fields.FloatField(default=datetime.datetime.timestamp(datetime.datetime.now()))
	status_message = fields.StringField()
	created_at = fields.DateTimeField(default=datetime.datetime.utcnow)
