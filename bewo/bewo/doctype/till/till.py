# -*- coding: utf-8 -*-
# Copyright (c) 2015, Indictrans and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import get_datetime

class Till(Document):
	def before_insert(self):
		""" update item sync date """

		item_modified_date = frappe.db.get_all("Item", fields="min(modified) as modified")
		if item_modified_date and item_modified_date[0]:
			self.item_sync_date = item_modified_date[0].get("modified")
		else:
			self.item_sync_date = get_datetime("1990-07-24 16:00:00")


def update_till_item_download_date(till, date):
	""" update till's item sync date and"""

	till = frappe.get_doc("Till", till)

	till.item_sync_date = date
	till.last_download_sync = get_datetime()

	till.save(ignore_permissions=True)