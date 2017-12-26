# encoding=utf-8

import re
import json
import time
import logging
from datetime import datetime

from tornado import gen
from tornado.web import asynchronous

import handler.base
from tasks import wechat
from models.wx_msg import WxMsgSendDetailModel, WxMsgStats


class SendTextHandler(handler.base.BaseHandler):
	
	def initialize(self):
		super(SendTextHandler, self).initialize()
		self.wxModel = WxMsgSendDetailModel()
		self.p_jmx = re.compile("(.+?) JMX is not reachable")
		self.p_agent = re.compile("Zabbix agent on (.+?) is unreachable for 5 minutes")
		self.p_time = re.compile("(.+?) Host local time error")

	
	@asynchronous
	@gen.coroutine
	def get(self):
		args = self.request.arguments
		logging.info('arguments sync: %s' % json.dumps(args))
		
		user_str = self.get_argument("to_user", None)
		content = self.get_argument("content", None)
		content = json.loads(content)
		event_id = content['eventid']
		status = content['status']
		trigger_name = content['trigger_name']

		is_match = self.p_jmx.search(trigger_name) or self.p_agent.search(trigger_name) or self.p_time.search(trigger_name)
		if is_match:
			self.write(json.dumps(dict(errCode = 0, errMsg='pass')))
			self.finish()
			return

		if None in [user_str, trigger_name]:
			ret = dict(errCode=10001, errMsg='Missing parameter to_user/content')
			self.write(json.dumps(ret))
			self.finish()
			return
		
		try:
			self.wxModel.content = trigger_name
			self.wxModel.send_to = user_str
			self.wxModel.clock = int(time.time())
			self.wxModel.uptime = int(time.time())
			self.wxModel.save()
			issue_id = self.wxModel.id
		except Exception, e:
			logging.error('Message content saved failed:%s' % str(e))

		users = user_str.split(',') if not isinstance(user_str, list) else user_str
		
		if self._redis and self._redis.get('add_link') and status in [0, '0']:
			link_str = "<a href='http://%s/issue/%s'>Click</a>" % ("http://alert.ane56.com", event_id)
			trigger_name = '%s %s' % (trigger_name, link_str)
		
		if status in [1, '1']:
			trigger_name = '%s %s' % (trigger_name, '<已恢复>')

		status, resp = self.wcep.send_msg2user(self.access_token, trigger_name, to_user=users, to_ptmt=None)
		if not status:
			logging.error('Response from wx: ' + json.dumps(resp))
			ret = dict(errCode = 10002, errMsg = resp)
		else:
			ret = dict(errCode = 0, errMsg='')
		

		self.write(json.dumps(ret))
		self.finish()
		
		
	def post(self):
		self.get()
		
		

class SendTextAsyncHandler(handler.base.BaseHandler):

	def initialize(self):
		super(SendTextAsyncHandler, self).initialize()
		self.p_jmx = re.compile("(.+?) JMX is not reachable")
		self.p_agent = re.compile("Zabbix agent on (.+?) is unreachable for 5 minutes")
		self.p_time = re.compile("(.+?) Host local time error")

		
	def get(self):
		args = self.request.arguments
		logging.info('arguments async: %s' % json.dumps(args))
		
		content = self.get_argument('content', None)
		content = json.loads(content)
		
		trigger_name = content['trigger_name']
		host = content['host']
		hostname = content['hostname']
		ip = content['ip']
		hostgroup = content['hostgroup']
		event_id = content['eventid']
		status = int(content['status'])
		severity = content['serverity']
		trigger_id = content['trigger_id']
		
		dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		tok = self._get_tts_tok()
		data = dict(host = hostname, content = trigger_name, dt = dt, 
				eventid = event_id, status = status, tok = tok, is_sound = 1, severity = severity, duration = '5s')

		is_match = self.p_jmx.search(trigger_name) or self.p_agent.search(trigger_name) or self.p_time.search(trigger_name)
		if is_match:
			self._agg(content)
			self.write(json.dumps(dict(errCode = 0, errMsg = 'pass')))
			self.finish()
			return

		user_str = self.get_argument('to_user', None)
		if None in [content, user_str]:
			self.write(json.dumps(dict(errCode = 10001, errMsg = 'Missing parameter to_user/content')))
			self.finish()
			return

		self._redis.publish('alert_channel', json.dumps(data))

		if status in [1, '1']:
			self._del_alert(event_id)
			self.write(json.dumps(dict(errCode = 0, errMsg = 'status == 1 and pass')))
			self.finish()
			return
		else:
			self._add_alert(data)

		users = user_str.split(',')
		#resp = wechat.send_wx_msg.delay(self.access_token, trigger_name, users)
		resp = dict(errCode = 0, errMsg = '')

		issue_id = 0
		try:
			model = WxMsgStats()
			model.content = trigger_name
			model.send_to = user_str
			model.clock = int(time.time())
			model.uptime = int(time.time())
			model.eventid = event_id
			model.host_group = hostgroup
			model.host = host
			model.hostname = hostname
			model.ip = ip
			model.trigger_id = trigger_id
			
			model.save()
			issue_id = model.id
		except Exception, e:
			logging.error('Message content saved failed:%s' % str(e))
	
		if self._redis and self._redis.get('link') and issue_id != 0:
			link = "<a href='http://%s/issue/%s'>点我</a>" % (self.request.headers.get('Host'), issue_id)

		ret = dict(errCode = 0, errMsg = str(resp))
		self.write(json.dumps(ret))


	def post(self):
		self.get()
	

	def _add_alert(self, data):
		self._redis.hset('alerts', str(data['eventid']), json.dumps(data))

	
	def _del_alert(self, event_id):
		self._redis.hdel('alerts', str(event_id))

	
	def _agg(self, content):
		trigger_name = content['trigger_name']
		eventid = int(content['eventid'])
		key = 'alertjmx' if self.p_jmx.search(trigger_name) else 'alertagent'
		ct = int(time.time())
		self._redis.zadd(key, eventid, ct)
	

		
class DepartmentHandler(handler.base.BaseHandler):
	
	def initialize(self):
		super(DepartmentHandler, self).initialize()
		
		
	def get(self):
		status, resp = self.wcep.get_department_list(self.access_token)
		self.write(json.dumps(dict(status=status, resp=resp)))
		
		

class UserHandler(handler.base.BaseHandler):
	
	def initialize(self):
		super(UserHandler, self).initialize()
		
		
	def get(self):
		userid = self.get_argument("userid")
		status, resp = self.wcep.get_user(self.access_token, userid)
		self.write(json.dumps(dict(status=status, resp=resp)))
	
	
	def post(self):
		userid = self.get_argument("userid")
		name = self.get_argument("name")
		department = department = self.get_argument("department")
		mobile = self.get_argument("mobile")
		
		data = dict(userid=userid, name=name, mobile=mobile, department=department)
		
		status, resp = self.wcep.create_user(self.access_token, data)
				
		self.write(json.dumps(dict(status=status, resp=resp)))
		self.finish()


class TagHandler(handler.base.BaseHandler):

	def initialize(self):
		super(TagHandler, self).initialize()

	
	def get(self):
		status, resp = self.wcep.get_tag(self.access_token, 1)
		self.write(json.dumps(dict(status=status, resp=resp)))
		self.finish()


	
class TestHandler(handler.base.BaseHandler):

	def initialize(self):
		super(TestHandler, self).initialize()


	def get(self):
		wechat.alert_agg.delay()
