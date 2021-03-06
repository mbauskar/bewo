import frappe
import json

from store import validate_store
from device import validate_device
from request import validate_request
from bewo.utils.sales_utils import validate_sales_record, create_invoice

@frappe.whitelist()
def addSalesRecords(data):
	"""parse sales data from bewo pos devices and create sales log"""
	try:
		args = json.loads(data)
		validate_request("add_sales", args)

		store = args.pop("store")
		device = args.pop("device")

		if all([store, device]):
			validate_store(store)
			validate_device(store, device)

			return validate_create_invoices(args, device)
		else:
			raise Exception("Invalid Store / Device ID")

	except Exception, e:
		raise e

def validate_create_invoices(args, device):
	""" validate and save invoices """
	response = []
	sales = args.pop("sales")
	if not sales:
		raise Exception("Sales Record not found")

	for record in sales:
		res = validate_sales_record(record)
		
		if not res.get("is_valid"):
			bill_no = record.get("strBillNumber")
			response.append({
				bill_no: {
					"invStatus": 500,
					"errors": res.get("errors")
				}
			})
		else:
			res = create_invoice(record, device)
			response.append(res)

	return response