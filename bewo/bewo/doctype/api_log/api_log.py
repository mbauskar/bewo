# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

import json
from datetime import datetime
from frappe.model.naming import make_autoname
from frappe.utils import get_datetime, format_datetime, nowdate, nowtime, to_timedelta

class APILog(Document):
	""" Create and update API Log """

	def autoname(self):
		name = "Log-{}-".format(datetime.strftime(get_datetime(), "%d%m%y"))
		self.name = make_autoname(name+'.#####')



def log_request(request, form_dict):
	""" Create new request log """

	log = frappe.new_doc("API Log")
	
	log.request_date = nowdate()
	log.request_time = nowtime()
	log.request_method = request.method
	log.request_url = request.url
	log.request_body = json.dumps(json.loads(form_dict.data), indent=2) \
		if form_dict and form_dict.data else json.dumps(form_dict, indent=2)

	log.owner = frappe.session.user

	log.save(ignore_permissions=True)
	return log.name

def log_response(docname, response=None):
	""" update the response for the request """

	res = json.loads(response)
	log = frappe.get_doc("API Log", docname)

	log.response_time = nowtime()
	log.response_date = nowdate()
	log.request_status = "Success" if res.get("code") == 200 else "Failed"
	log.response = json.dumps(res, indent=2)
	log.execution_time = "{0}".format(to_timedelta(log.response_time) - log.request_time)

	log.save(ignore_permissions=True)
	frappe.db.commit()