# Copyright (c) 2026, Portales Web and contributors
# For license information, please see license.txt

from __future__ import annotations

import hashlib
import re

import frappe
from frappe import _
from frappe.model.document import Document


ACTIVE_RESERVATION_STATUSES = ("Registrada", "En revisión", "Observada")
FINAL_STATUS_BY_DOCSTATUS = {1: "Procesada", 2: "Rechazada"}


def normalize_bill_no(value: str) -> str:
	"""Return a stable invoice identifier without trusting browser formatting."""
	cleaned = re.sub(r"\s+", "", str(value or "").strip().upper())
	if not cleaned or len(cleaned) > 140:
		frappe.throw(_("Ingrese un número de factura válido."))
	return cleaned


def make_supplier_invoice_key(supplier: str, normalized_bill_no: str) -> str:
	value = f"{supplier}\0{normalized_bill_no}".encode()
	return hashlib.sha256(value).hexdigest()


class SupplierInvoiceSubmission(Document):
	def validate(self):
		self.normalized_bill_no = normalize_bill_no(self.bill_no)
		self.supplier_invoice_key = make_supplier_invoice_key(self.supplier, self.normalized_bill_no)

	def on_trash(self):
		if self.purchase_invoice:
			frappe.throw(_("No se puede eliminar un registro vinculado a una Factura de Compra."))


def has_website_permission(doc, ptype, user, verbose=False):
	if not user or user == "Guest":
		return False

	portal_user = frappe.qb.DocType("Portal User")
	authorized = (
		frappe.qb.from_(portal_user)
		.select(portal_user.parent)
		.where(portal_user.user == user)
		.where(portal_user.parenttype == "Supplier")
		.where(portal_user.parent == doc.supplier)
	).run()
	return bool(authorized)


def sync_purchase_invoice_status(doc, method=None):
	status = "Rechazada" if method == "on_trash" else FINAL_STATUS_BY_DOCSTATUS.get(doc.docstatus)
	if not status:
		return

	name = frappe.db.get_value(
		"Supplier Invoice Submission", {"purchase_invoice": doc.name}, "name"
	)
	if not name:
		return

	submission = frappe.get_doc("Supplier Invoice Submission", name)
	if submission.status != status:
		submission.status = status
		submission.save(ignore_permissions=True)
