import json
import frappe

def get_inventory_records(item_code=None, fields=None, filters=None, order_by=None,	limit_start=None,
	limit_page_length=20):
	from test_records import records

	fields = [
		"name as strProductCode",
		"item_name as strProductName",
		"ifnull(brand, '') as strBrand",
		"ifnull(category, '') as strCategory",
		"ifnull(mrp,0) as dblMRP",
		"ifnull(retail_rate, 0) as dblSellingPrice_Retail",
		"ifnull(wholesale_rate, 0) as dblSellingPrice_Wholesale",
		"ifnull(purchase_rate, 0) as dblPurchasePrice",
		"ifnull(inventory_maintained_by, '') as type",
		"case disabled when 0 then 'Active' else 'Deactive' end as staus",
		"'%s' as strCompany"%(frappe.db.get_default("company")),
		"variant_of"
	]

	if item_code:
		if not frappe.db.get_value("Item", item_code, "name"):
			raise Exception("%s Item not available"%item_code)

		variants = frappe.db.get_value("Item", item_code, ["has_variants", "variant_of"], as_dict=True)
		if variants.get("variant_of"):
			item_code = variants.get("variant_of")
		
		filters = [["Item", "item_code", "=", item_code]]
		item = frappe.get_list("Item", fields=fields, filters=filters)
		item[0].pop("variant_of")
		prices = frappe.db.get_values("Item", { "variant_of":item_code }, "mrp")
		item[0].update({ "dblMRP": [price[0] for price in prices] })
		return { "inventory":item }
	else:
		prices = {}
		_filters = [] if not filters else json.loads(filters)
		_filters.append(["Item", "has_variants", "=", 0])

		try:
			items = frappe.get_list("Item", fields=fields, filters=_filters, order_by=order_by,
				limit_start=limit_start, limit_page_length=limit_page_length)

			for item in items:
				variant_of = item.pop("variant_of")
				if variant_of:
					mrp = [] if not prices.get(variant_of) else prices.get(variant_of)
					mrp.append(item.get("dblMRP"))
					prices.update({ variant_of: mrp})

					del items[items.index(item)]

			_filters = [] if not filters else json.loads(filters)
			_filters.append(["Item", "has_variants", "=", 1])
			
			template_items = frappe.get_list("Item", fields=fields, filters=_filters, order_by=order_by,
				limit_start=limit_start, limit_page_length=limit_page_length)

			for item in template_items:
				item.update({ "dblMRP": prices.get(item.get("strProductCode")) })

			items.extend(template_items)

			return {"inventory": items}
		except Exception, e:
			raise Exception("Error while fetching Items %s"%(e.message))