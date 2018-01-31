# encoding=utf-8

import json
import time
import logging

import handler.base
from tasks import wechat
from models.wx_msg import WxMsgSendDetailModel


class TestHandler(handler.base.BaseHandler):
	
	def initialize(self):
		super(TestHandler, self).initialize()
	
	
	def get(self):
		content = self.get_argument('content', None)
		user_str = self.get_argument('to_user', None)
		if None in [content, user_str]:
			self.write(json.dumps(dict(errCode = 10001, errMsg = 'Missing parameter to_user/content')))
			return

		users = user_str.split('|')
		ts = self.ts2str(time.time())
		#resp = wechat.send_wx_msg.delay(self.access_token, content, users)
		kwargs = dict(title='告警消息',description = "<div class=\"gray\">"+ts+"</div><div class=\"highlight\">"+content+"</div>", url='https://m.baidu.com')
		status, resp = self.wcep.send_msg2user(self.access_token, content, to_user=users, msg_type="textcard", to_ptmt=None, **kwargs)
		self.write(str(resp))


	def post(self):
		self.get()


class ModelTestHandler(handler.base.BaseHandler):

	def initialize(self):
		super(ModelTestHandler, self).initialize()
		self.wxModel = WxMsgSendDetailModel()

	def get(self):
		content = self.get_argument('content', 'xxx')
		send_to = 'heruihong'
		event_id = 110
		self.wxModel.content = content
		self.wxModel.send_to = send_to
		self.wxModel.event_id = event_id

		self.wxModel.save()
