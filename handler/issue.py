# encoding=utf-8


import json
import time
import logging
import datetime


#from playhouse.shortcuts import model_to_dict

import handler.base
from models.issue import IssueTypeModel
from models.alert import AlertIgnore
from models.wx_msg import WxMsgStats, WxMsgSendDetailModel


class IssueHandler(handler.base.BaseHandler):

	def initialize(self):
		super(IssueHandler, self).initialize()
		self.wxModel = WxMsgStats()
		self.isModel = IssueTypeModel

	def get(self, event_id):
		ft = WxMsgStats.eventid == event_id
		try:
			issue = WxMsgStats.get(ft)

			clock = int(issue.clock)
			clock = datetime.datetime.fromtimestamp(clock).strftime('%Y-%m-%d %H:%M:%S')
			issue.clock = clock

			types = self.isModel.select()
		except:
			issue = None
			raise
		
		self.render('issue.html', issue = issue, types = types, title = 'Confirm')


	def post(self, event_id):
		process_status = self.get_argument('process_status')
		
		ft = WxMsgStats.eventid == event_id
		issue = WxMsgStats.get(ft)
		issue.uptime = int(time.time())
		issue.process_status = process_status

		try:
			issue.save()
			
			if process_status in [2, '2']:
				ignore_to = self.get_argument('ignore_to')
				am = AlertIgnore()
				am.creator = self.userid
				am.trigger_id = iss.trigger_id
				am.save()
			ret = dict(errCode = 0, errMsg = '')
		except Exception, e:
			ret = dict(errCode = 110, errMsg = str(e))

		self.write(json.dumps(ret))
