# Copyright (c) 2026, Portales Web and contributors
# For license information, please see license.txt

from urllib.parse import urlencode

import frappe

from portales_web.api.supplier_portal import get_effective_supplier


no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?" + urlencode(
			{"redirect-to": "/registrar-factura"}
		)
		raise frappe.Redirect

	supplier = get_effective_supplier()
	context.title = "Registrar factura"
	context.no_breadcrumbs = True
	context.show_sidebar = True
	context.supplier = supplier
	context.supplier_name = frappe.db.get_value("Supplier", supplier, "supplier_name") or supplier
	return context
