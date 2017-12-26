#!/opt/anaconda2/bin/python2.7
#encoding=utf-8

import time
import peewee

from .base import BaseModel



class AlertBlockModel(BaseModel):
	
	id = peewee.PrimaryKeyField()
	creator = peewee.CharField(max_length = 50)
	groupids = peewee.CharField(max_length = 100)
	hostids = peewee.CharField(max_length = 500)
	time_from = peewee.IntegerField()
	time_till = peewee.IntegerField()
	reason = peewee.IntegerField(default = 0)
	uptime = peewee.IntegerField(default = int(time.time()))
	active = peewee.IntegerField(default = 0)

	class Meta:
		db_table = 't_alert_block'



class AlertIgnore(BaseModel):

	id = peewee.PrimaryKeyField()
	createtime = peewee.IntegerField(default = int(time.time()))
	uptime = peewee.IntegerField(default = int(time.time()))
	trigger_id = peewee.IntegerField()
	ignore_to = peewee.IntegerField()
	creator = peewee.CharField(max_length = 50)

	class Meta:
		db_table = 't_alert_ignore'
