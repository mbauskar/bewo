import json
import frappe
from bewo.bewo.doctype.till.till import update_till_item_download_date

def get_inventory_records(item_code=None, device=None, fields=None, filters=None, order_by="modified asc",
	limit_start=None, limit_page_length=20):

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
		"variant_of",
		"modified"
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
		modified = []

		_filters = [] if not filters else json.loads(filters)
		_filters.append(["Item", "has_variants", "=", 0])

		# get last item sync date filter
		if device:
			last_max_synced = frappe.db.get_value("Till", device, "item_sync_date")
			_filters.append(["Item", "modified", ">", str(last_max_synced)])

		try:
			items = []
			items = frappe.get_list("Item", fields=fields, filters=_filters, order_by=order_by,
				limit_start=limit_start, limit_page_length=limit_page_length)

			if not items:
				return {"inventory": []}

			to_remove = []
			for item in items:
				variant_of = item.pop("variant_of")
				price = get_item_prices(item)
				
				modified_date = item.pop("modified")
				modified.append(modified_date)

				if variant_of:
					mrp = [] if not prices.get(variant_of) else prices.get(variant_of)
					mrp.append(price)
					prices.update({ variant_of: mrp})

					# del items[items.index(item)]
					to_remove.append(item)

				item.update({ "dblMRP": [price] })

			for item in to_remove:
				del items[items.index(item)]

			_filters = [] if not filters else json.loads(filters)
			_filters.append(["Item", "has_variants", "=", 1])

			# get last item sync date filter
			if device:
				last_max_synced = frappe.db.get_value("Till", device, "item_sync_date")
				_filters.append(["Item", "modified", ">", str(last_max_synced)])

			template_items = frappe.get_list("Item", fields=fields, filters=_filters, order_by=order_by,
				limit_start=limit_start, limit_page_length=limit_page_length)

			for item in template_items:
				variant_of = item.pop("variant_of")
				modified_date = item.pop("modified")
				modified.append(modified_date)
				get_item_prices(item)

				item.update({ "dblMRP": prices.get(item.get("strProductCode")) })

			# if device: update_till_item_download_date(device, max(modified))
			items.extend(template_items)

			return {"inventory": items}
		except Exception, e:
			raise Exception("Error while fetching Items %s"%(e.message))

def get_item_prices(item):
	dblMRP = item.pop("dblMRP")
	dblSellingPrice_Retail = item.pop("dblSellingPrice_Retail")
	dblSellingPrice_Wholesale = item.pop("dblSellingPrice_Wholesale")
	dblPurchasePrice = item.pop("dblPurchasePrice")

	return ",".join([
			str(dblMRP),
			str(dblSellingPrice_Retail),
			str(dblSellingPrice_Wholesale),
			str(dblPurchasePrice)
		])