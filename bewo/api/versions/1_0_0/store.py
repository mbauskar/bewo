import frappe
from inventory import get_inventory_records
from api_handler.api_handler.exceptions import *

from test_records import records, index_mapping

@frappe.whitelist()
def get(resource, device=None, fields=None, filters=None, limit_start=None, limit_page_length=20):
	store_id = txn = txn_id = None
	if not resource:
		raise InvalidDataError("Input not provided")

	if not device:
		raise InvalidDataError("Device ID not provided")

	if len(resource) >= 1:
		store_id = resource[0]

	if len(resource) >= 2:
		txn = resource[1]

	if len(resource) >= 3:
		txn_id = resource[2]

	validate_store(store_id)
	if not txn: txn = "inventory"
	# validate txn type
	validate_transaction_type(txn)
	try:
		if "count" in [txn, txn_id]:
			return get_count(store_id=store_id, txn=txn, txn_id=txn_id, fields=fields, filters=filters,
				limit_start=limit_start, limit_page_length=limit_page_length)
		else:
			return get_records(store_id=store_id, device=device, txn=txn, txn_id=txn_id, fields=fields, filters=filters,
				limit_start=limit_start, limit_page_length=limit_page_length)
	except Exception, e:
		import traceback
		print traceback.print_exc()
		raise e

def get_count(store_id=None, txn=None, txn_id=None, fields=None, filters=None, limit_start=None, limit_page_length=20):
	""" get total count of records"""
	from test_records import records, index_mapping

	if txn == txn_id:
		return InvalidURL("Invalid Input / URL")

	if all([txn, txn_id]):
		if txn == "count":
			return InvalidURL("Invalid URL")
		elif txn_id == "count":
			transactions = get_records(store_id=store_id, txn=txn, fields=fields, filters=filters,
							limit_start=limit_start, limit_page_length=limit_page_length) or {}
			if not transactions:
				return { "total_records": { txn: 0 } }
			else:
				return { "total_records": { txn: len(transactions.get(txn)) } }

def get_records(store_id=None, device=None, txn=None, txn_id=None, fields=None, filters=None, limit_start=None,
	limit_page_length=20):
	""" get the total records """
	try:
		return txn_methods[txn](item_code=txn_id, device=device, fields=fields, filters=filters,
				limit_start=limit_start, limit_page_length=limit_page_length)
	except Exception, e:
		raise Exception(e.message)

def validate_transaction_type(txn):
	if txn not in txn_methods.keys():
		raise Exception("Invalid transactions, Transactions should be (%s)"%(",".join(txn_methods.keys())))

def validate_store(store):
	""" validate store """
	# create Store Profile Single DocType save store ID to validate
	pass

txn_methods = {
	"inventory": get_inventory_records,
}