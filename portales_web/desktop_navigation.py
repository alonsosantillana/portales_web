"""Frappe v16 launcher visibility; reuse existing destination permissions."""

import frappe
from frappe.utils.modules import is_module_visible


def has_app_permission() -> bool:
	"""Return whether this System User can open the app's existing destination."""
	user = frappe.session.user
	if not user or user == "Guest":
		return False
	if frappe.get_cached_value("User", user, "user_type") != "System User":
		return False
	if "portales_web" not in frappe.get_installed_apps():
		return False
	if not frappe.db.exists("DocType", "Supplier Invoice Submission"):
		return False
	module = frappe.get_cached_value("DocType", "Supplier Invoice Submission", "module")
	if not module or not frappe.db.exists("Module Def", module):
		return False
	if not is_module_visible(module):
		return False
	return bool(frappe.has_permission("Supplier Invoice Submission", ptype="read"))
