import datetime

from umongo import Document, fields

from .common import instance


@instance.register
class Group(Document):
	tg_id = fields.IntegerField(unique=True, required=True)
	name = fields.StringField(required=True)
	group = fields.StringField(max_length=4)
	added_at = fields.DateTimeField(default=datetime.datetime.utcnow)
