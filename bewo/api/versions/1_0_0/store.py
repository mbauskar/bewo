import frappe
from inventory import get_inventory_records
from api_handler.api_handler.exceptions import *

from test_records import records, index_mapping

@frappe.whitelist()
def get(resource, fields=None, filters=None, order_by=None,	limit_start=None, limit_page_length=20):
	store_id = txn = txn_id = None
	if not resource:
		raise InvalidDataError("Input not provided")

	if len(resource) >= 1:
		store_id = resource[0]

	if len(resource) >= 2:
		txn = resource[1]

	if len(resource) >= 3:
		txn_id = resource[2]

	validate_store(store_id)
	validate_transaction_type(txn)
	# validate txn type

	if "count" in [txn, txn_id]:
		return get_count(store_id=store_id, txn=txn, txn_id=txn_id)
	else:
		return get_records(store_id=store_id, txn=txn, txn_id=txn_id, fields=fields, filters=filters,
			order_by=order_by,	limit_start=limit_start, limit_page_length=limit_page_length)

def get_count(store_id=None, txn=None, txn_id=None, fields=None,
	filters=None, order_by=None,	limit_start=None, limit_page_length=20):
	""" get total count of records"""
	from test_records import records, index_mapping

	if txn == txn_id:
		return InvalidURL("Invalid Input / URL")

	if all([txn, txn_id]):
		if txn == "count":
			return InvalidURL("Invalid URL")
		elif txn_id == "count":
			transactions = get_records(store_id=store_id, txn=txn, fields=fields, filters=filters,
							order_by=order_by,	limit_start=limit_start, limit_page_length=limit_page_length) or {}
			if not transactions:
				return { "total_records": { txn: 0 } }
			else:
				return { "total_records": { txn: len(transactions.get(txn)) } }

	elif txn and not txn_id:
		result = { txn:0 for txn in index_mapping }
		transactions = records.get(store_id) if records.get(store_id) else {}
		
		for txn, records in transactions.iteritems():
			result.update({ txn: len(records) })

		return { "total_records": result }

def get_records(store_id=None, txn=None, txn_id=None,
	fields=None, filters=None, order_by=None,	limit_start=None,
	limit_page_length=20):
	""" get the total records """
	try:
		return txn_methods[txn](item_code=txn_id, fields=fields, filters=filters, order_by=order_by,
				limit_start=limit_start, limit_page_length=limit_page_length)
	except Exception, e:
		raise Exception(e.message)

def validate_transaction_type(txn):
	if not txn:
		txn = "inventory"
	elif txn not in txn_methods.keys():
		raise Exception("Invalid transactions, Transactions should be (%s)"%(",".join(txn_methods.keys())))

def validate_store(store):
	""" validate store """
	# create Store Profile Single DocType save store ID to validate
	pass

txn_methods = {
	"inventory": get_inventory_records,
}