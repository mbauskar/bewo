import frappe

def validate_sales_record(sales_order, is_sales_return=False):
	""" validate product, product stock, bill number """

	def append_errors(result, res):
		errors = result.get("errors") or []
		if not errors:
			errors = [res.get("error")]
		else:
			errors.extend(res.get("error"))
		return errors

	result = { "is_valid": True }
	bill_no = sales_order.get("strBillNumber")
	invoice = ""

	res = validate_bill_number(bill_no, is_sales_return=is_sales_return)
	if not res.get("is_valid"):
		result.update({ "is_valid": False, "errors": append_errors(result, res) })

	res = validate_products(sales_order.get("products"), bill_no=bill_no, is_sales_return=is_sales_return)
	if not res.get("is_valid"):
		result.update({ "is_valid": False, "errors": append_errors(result, res) })

	return result

def validate_fiscal_year(date):
	pass

def validate_bill_number(bill_no, is_sales_return=False):
	""" check if with same bill no already one invoice is available """
	result = {
		"is_valid": True
	}

	if not is_sales_return:
		invoices = frappe.db.get_values("Sales Invoice", { "bill_number": bill_no }, "name", as_dict=True)
		if invoices:
			si_names = [si.get("name") for si in invoices]
			error_msg = "{} invoice(s) is already created for bill number {}".format(",".join(si_names), bill_no)

			result.update({
				"is_valid": False,
				"error": error_msg
			})
	else:
		invoice = frappe.db.get_value("Sales Invoice", { "bill_number": bill_no }, "name", as_dict=True)
		if not invoice:
			error_msg = "Invoice For Bill No. {}  Not Found"

			result.update({
				"is_valid": False,
				"error": error_msg
			})
		else:
			result.update({ "sales_invoice": invoice.get("name") })

	return result

def validate_products(products, bill_no=None, is_sales_return=False):
	""" check if product is available and check the stock """

	if not products:
		raise Exception("Invalid Products value")

	invalid_items = []
	
	# for sales return items validation
	invalid_return_items = []
	invalid_return_qty_items = []
	invalid_return_rate_items = []

	for item in products:
		if not frappe.db.get_value("Item", item.get("strProductCode"), "name"):
			invalid_items.append(item.get("strProductCode"))

		if all([is_sales_return, item.get("strProductCode") not in invalid_items]):
			invoice = frappe.db.get_value("Sales Invoice", { "bill_number": bill_no }, "name", as_dict=True)
			filters = {
				"parent": invoice.get("name"),
				"item_code": item.get("strProductCode")
			}
			inv_item = frappe.db.get_value("Sales Invoice Item", filters, ["item_code", "qty", "rate"], as_dict=True)

			if not inv_item:
				invalid_return_items.append(item.get("strProductCode"))
			if inv_item.get("qty") < item.get("strQty"):
				invalid_return_qty_items.append(item.get("strProductCode"))
			if inv_item.get("rate") < item.get("dblMRP"):
				invalid_return_rate_items.append(item.get("strProductCode"))

	if any([invalid_items, invalid_return_items, invalid_return_qty_items]):
		result = { "is_valid": False }
		errors = []

		if invalid_items: errors.append("Invalid Items : ({})".format(",".join(invalid_items)))
		if invalid_return_items: errors.append("Item ({}) not Found in Sales Order : {}".format(
					",".join(invalid_return_items),
					bill_no
				))
		if invalid_return_qty_items: errors.append("Invalid Qty for Sales Return Item(s) ({})".format(
				",".join(invalid_return_qty_items)
			))
		if invalid_return_rate_items: errors.append("Sales Return rate is greater than Sales Order rate for Item(s) ({})".format(
				",".join(invalid_return_rate_items)
			))

		result.update({ "error": errors })
		return result
	else:
		return { "is_valid": True }

def create_invoice(sales_order, device):
	""" create new Sales Invoice """
	record = {}
	bill_no = sales_order.get("strBillNumber")
	try:
		doc = frappe.new_doc("Sales Invoice")
		doc.naming_series = "SINV-"
		doc.posting_date = sales_order.get("date")
		doc.due_date = sales_order.get("date")
		doc.bill_number = bill_no
		doc.device = device
		doc.customer = "Retail Customer"
		doc.update_stock = 1
		doc.is_pos = 1

		# setting up the items
		doc.set("items", [])
		for product in sales_order.get("products"):
			item = doc.append("items", {})

			item.item_code = product.get("strProductCode")
			item.item_name = product.get("strItemName")
			item.qty = product.get("strQty")
			item.rate = product.get("dblMRP")

		doc.owner = frappe.session.user
		doc.submit()

		return {
			bill_no: { 
				"invStatus": 200,
				"message": "Invoice Created",
				"strInvoiceDate": doc.creation,
				"strERPBillNumber": doc.name
			}
		}
	except Exception, e:
		return {
			bill_no: { 
				"invStatus": 500,
				"message": "Error while creating Invoice",
				"errors": e.message
			}
		}

def create_sales_return_invoice(sales_return, device, sales_invoice):
	""" make sales return """
	from frappe.utils import nowdate, nowtime
	from erpnext.controllers.sales_and_purchase_return import make_return_doc
	
	bill_no = sales_return.get("strBillNumber")
	try:
		doc = make_return_doc("Sales Invoice", sales_invoice, target_doc=None)

		# doc.posting_date = sales_return.get("date")
		doc.posting_date = nowdate()
		doc.posting_time = nowtime()
		items_to_return = { item.get("strProductCode"):item for item in sales_return.get("products") }
		
		to_remove = []
		for item in doc.items:
			# update item qty, rate and removed items that are not in sales return
			if item.item_code not in items_to_return.keys():
				to_remove.append(item)
			else:
				item.qty = items_to_return.get(item.item_code).get("strQty") * -1
				item.rate = items_to_return.get(item.item_code).get("dblMRP")

		if to_remove: [doc.remove(item) for item in to_remove]

		doc.owner = frappe.session.user
		doc.submit()

		return {
			bill_no: {
				"invStatus": 200,
				"message": "Sales Return Created",
				"strInvoiceDate": doc.creation,
				"strERPBillNumber": doc.name
			}
		}
	except Exception, e:
		return {
			bill_no: { 
				"invStatus": 500,
				"message": "Error while creating Invoice",
				"errors": e.message
			}
		}