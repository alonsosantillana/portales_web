# Copyright (c) 2026, Portales Web and contributors
# For license information, please see license.txt

from __future__ import annotations

import base64
import binascii
import math
from pathlib import PurePath

import frappe
from erpnext.accounts.party import get_payment_terms_template
from erpnext.buying.doctype.purchase_order.purchase_order import get_mapped_purchase_invoice
from erpnext.controllers.website_list_for_contact import get_parents_for_user
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
	get_invoiced_qty_map,
	get_returned_qty_map,
)
from frappe import _
from frappe.core.api.file import get_max_file_size
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder.functions import Replace, Sum, Trim, Upper
from frappe.rate_limiter import rate_limit
from frappe.utils import flt, getdate, nowdate
from frappe.utils.file_manager import save_file

from portales_web.portales_web.doctype.supplier_invoice_submission.supplier_invoice_submission import (
	ACTIVE_RESERVATION_STATUSES,
	SOURCE_PURCHASE_ORDER,
	SOURCE_PURCHASE_RECEIPT,
	make_supplier_invoice_key,
	normalize_bill_no,
)


SUBMISSION_DOCTYPE = "Supplier Invoice Submission"
SUBMISSION_ITEM_DOCTYPE = "Supplier Invoice Submission Item"
MAX_ITEMS_PER_SUBMISSION = 200
FISCAL_INVOICE_CODE = "01"
FISCAL_FIELDS = {
	"tipo_comprobante",
	"codigo_comprobante",
	"tipo_documento_identidad",
	"codigo_tipo_documento",
}


@frappe.whitelist()
def get_supplier_context():
	supplier = get_effective_supplier()
	return {
		"supplier": supplier,
		"supplier_name": frappe.db.get_value("Supplier", supplier, "supplier_name") or supplier,
	}


@frappe.whitelist()
def get_eligible_purchase_orders(limit_start=0, limit_page_length=50):
	supplier = get_effective_supplier()
	limit_start, limit_page_length = _pagination(limit_start, limit_page_length)

	return frappe.get_all(
		"Purchase Order",
		filters={
			"supplier": supplier,
			"docstatus": 1,
			"status": ["!=", "Closed"],
			"per_billed": ["<", 100],
		},
		fields=[
			"name",
			"transaction_date",
			"schedule_date",
			"company",
			"currency",
			"grand_total",
			"per_billed",
			"status",
		],
		order_by="transaction_date desc, name desc",
		limit_start=limit_start,
		limit_page_length=limit_page_length,
	)


@frappe.whitelist()
def get_purchase_order_items(purchase_order: str):
	supplier = get_effective_supplier()
	po = _get_authorized_purchase_order(purchase_order, supplier)
	items = _get_item_availability(po)

	return {
		"purchase_order": po.name,
		"supplier": po.supplier,
		"company": po.company,
		"currency": po.currency,
		"grand_total": po.grand_total,
		"items": [item for item in items if item["available_qty"] > 0],
	}


@frappe.whitelist()
def get_eligible_purchase_receipts(limit_start=0, limit_page_length=50):
	supplier = get_effective_supplier()
	limit_start, limit_page_length = _pagination(limit_start, limit_page_length)
	candidates = frappe.get_all(
		"Purchase Receipt",
		filters={
			"supplier": supplier,
			"docstatus": 1,
			"is_return": 0,
			"status": ["!=", "Closed"],
			"per_billed": ["<", 100],
		},
		fields=[
			"name",
			"posting_date",
			"supplier_delivery_note",
			"company",
			"currency",
			"grand_total",
			"per_billed",
			"status",
		],
		order_by="posting_date desc, name desc",
		limit_start=limit_start,
		limit_page_length=min(max(limit_page_length * 2, 50), 200),
	)

	eligible = []
	for receipt in candidates:
		pr = frappe.get_doc("Purchase Receipt", receipt.name)
		if any(item["available_qty"] > 0 for item in _get_purchase_receipt_item_availability(pr)):
			eligible.append(receipt)

	return eligible[:limit_page_length]


@frappe.whitelist()
def get_purchase_receipt_items(purchase_receipt: str):
	supplier = get_effective_supplier()
	pr = _get_authorized_purchase_receipt(purchase_receipt, supplier)
	items = _get_purchase_receipt_item_availability(pr)

	return {
		"purchase_receipt": pr.name,
		"supplier": pr.supplier,
		"company": pr.company,
		"currency": pr.currency,
		"grand_total": pr.grand_total,
		"items": [item for item in items if item["available_qty"] > 0],
	}


@frappe.whitelist()
def get_my_submissions(limit_start=0, limit_page_length=20):
	supplier = get_effective_supplier()
	limit_start, limit_page_length = _pagination(limit_start, limit_page_length)

	rows = frappe.get_all(
		SUBMISSION_DOCTYPE,
		filters={"supplier": supplier},
		fields=[
			"name",
			"source_type",
			"purchase_order",
			"purchase_receipt",
			"bill_no",
			"bill_date",
			"currency",
			"declared_total",
			"expected_total",
			"variance",
			"status",
			"purchase_invoice",
			"creation",
		],
		order_by="creation desc",
		limit_start=limit_start,
		limit_page_length=limit_page_length,
	)
	for row in rows:
		row.source_type = row.source_type or SOURCE_PURCHASE_ORDER
		row.source_name = row.purchase_receipt or row.purchase_order
	return rows


@frappe.whitelist(methods=["POST"])
@rate_limit(key="supplier_invoice_submission", limit=10, seconds=60)
def submit_invoice(
	purchase_order: str,
	bill_no: str,
	bill_date: str,
	declared_total,
	items,
	invoice_pdf,
	invoice_xml,
	supplier_remarks: str | None = None,
):
	"""Create one audited portal submission and one Purchase Invoice Draft."""
	user = _require_supplier_user()
	supplier = get_effective_supplier()
	clean_bill_no = str(bill_no or "").strip()
	if len(clean_bill_no) > 140:
		frappe.throw(_("El número de factura no puede superar 140 caracteres."))
	normalized_bill_no = normalize_bill_no(clean_bill_no)
	invoice_key = make_supplier_invoice_key(supplier, normalized_bill_no)
	clean_bill_date = _validate_bill_date(bill_date)
	clean_declared_total = _positive_number(declared_total, _("El total declarado debe ser mayor que cero."))
	clean_remarks = _clean_remarks(supplier_remarks)
	requested_items = _parse_requested_items(items)
	pdf_name, pdf_content = _decode_attachment(invoice_pdf, ".pdf")
	xml_name, xml_content = _decode_attachment(invoice_xml, ".xml")

	existing = _get_existing_submission(invoice_key)
	if existing:
		return _existing_submission_response(existing)

	_validate_purchase_invoice_duplicate(supplier, normalized_bill_no)
	_lock_purchase_order(purchase_order)
	po = _get_authorized_purchase_order(purchase_order, supplier)
	available_items = {row["purchase_order_item"]: row for row in _get_item_availability(po)}
	validated_items = _validate_requested_items(requested_items, available_items)

	request_doc = frappe.get_doc(
		{
			"doctype": SUBMISSION_DOCTYPE,
			"supplier": supplier,
			"source_type": SOURCE_PURCHASE_ORDER,
			"purchase_order": po.name,
			"company": po.company,
			"bill_no": clean_bill_no,
			"bill_date": clean_bill_date,
			"submitted_by": user,
			"currency": po.currency,
			"declared_total": clean_declared_total,
			"status": "Registrada",
			"supplier_remarks": clean_remarks,
			"normalized_bill_no": normalized_bill_no,
			"supplier_invoice_key": invoice_key,
			"items": validated_items,
		}
	)

	try:
		request_doc.insert(ignore_permissions=True, ignore_mandatory=True)
	except frappe.DuplicateEntryError:
		existing = _get_existing_submission(invoice_key)
		if existing:
			return _existing_submission_response(existing)
		raise

	pi = _make_purchase_invoice(po, normalized_bill_no, clean_bill_date, validated_items, request_doc.name)
	pdf_file = save_file(pdf_name, pdf_content, "Purchase Invoice", pi.name, is_private=1)
	xml_file = save_file(xml_name, xml_content, "Purchase Invoice", pi.name, is_private=1)

	request_doc.invoice_pdf = pdf_file.file_url
	request_doc.invoice_xml = xml_file.file_url
	request_doc.purchase_invoice = pi.name
	request_doc.expected_total = flt(pi.grand_total, pi.precision("grand_total"))
	request_doc.variance = flt(
		request_doc.declared_total - request_doc.expected_total,
		request_doc.precision("variance"),
	)
	request_doc.status = "En revisión"
	request_doc.save(ignore_permissions=True)

	return {
		"submission": request_doc.name,
		"purchase_invoice": pi.name,
		"docstatus": pi.docstatus,
		"status": request_doc.status,
		"expected_total": request_doc.expected_total,
		"variance": request_doc.variance,
		"duplicate": False,
	}


@frappe.whitelist(methods=["POST"])
@rate_limit(key="supplier_receipt_invoice_submission", limit=10, seconds=60)
def submit_invoice_from_receipt(
	purchase_receipt: str,
	bill_no: str,
	bill_date: str,
	declared_total,
	items,
	invoice_pdf,
	invoice_xml,
	supplier_remarks: str | None = None,
):
	"""Create one audited portal submission and Purchase Invoice Draft from a receipt."""
	user = _require_supplier_user()
	supplier = get_effective_supplier()
	clean_bill_no = str(bill_no or "").strip()
	if len(clean_bill_no) > 140:
		frappe.throw(_("El número de factura no puede superar 140 caracteres."))
	normalized_bill_no = normalize_bill_no(clean_bill_no)
	invoice_key = make_supplier_invoice_key(supplier, normalized_bill_no)
	clean_bill_date = _validate_bill_date(bill_date)
	clean_declared_total = _positive_number(declared_total, _("El total declarado debe ser mayor que cero."))
	clean_remarks = _clean_remarks(supplier_remarks)
	requested_items = _parse_requested_receipt_items(items)
	pdf_name, pdf_content = _decode_attachment(invoice_pdf, ".pdf")
	xml_name, xml_content = _decode_attachment(invoice_xml, ".xml")

	existing = _get_existing_submission(invoice_key)
	if existing:
		return _existing_submission_response(existing)

	_validate_purchase_invoice_duplicate(supplier, normalized_bill_no)
	_lock_purchase_receipt(purchase_receipt)
	pr = _get_authorized_purchase_receipt(purchase_receipt, supplier)
	available_items = {
		row["purchase_receipt_item"]: row for row in _get_purchase_receipt_item_availability(pr)
	}
	validated_items = _validate_requested_receipt_items(requested_items, available_items)

	request_doc = frappe.get_doc(
		{
			"doctype": SUBMISSION_DOCTYPE,
			"supplier": supplier,
			"source_type": SOURCE_PURCHASE_RECEIPT,
			"purchase_receipt": pr.name,
			"company": pr.company,
			"bill_no": clean_bill_no,
			"bill_date": clean_bill_date,
			"submitted_by": user,
			"currency": pr.currency,
			"declared_total": clean_declared_total,
			"status": "Registrada",
			"supplier_remarks": clean_remarks,
			"normalized_bill_no": normalized_bill_no,
			"supplier_invoice_key": invoice_key,
			"items": validated_items,
		}
	)

	try:
		request_doc.insert(ignore_permissions=True, ignore_mandatory=True)
	except frappe.DuplicateEntryError:
		existing = _get_existing_submission(invoice_key)
		if existing:
			return _existing_submission_response(existing)
		raise

	pi = _make_purchase_invoice_from_receipt(
		pr, normalized_bill_no, clean_bill_date, validated_items, request_doc.name
	)
	pdf_file = save_file(pdf_name, pdf_content, "Purchase Invoice", pi.name, is_private=1)
	xml_file = save_file(xml_name, xml_content, "Purchase Invoice", pi.name, is_private=1)

	request_doc.invoice_pdf = pdf_file.file_url
	request_doc.invoice_xml = xml_file.file_url
	request_doc.purchase_invoice = pi.name
	request_doc.expected_total = flt(pi.grand_total, pi.precision("grand_total"))
	request_doc.variance = flt(
		request_doc.declared_total - request_doc.expected_total,
		request_doc.precision("variance"),
	)
	request_doc.status = "En revisión"
	request_doc.save(ignore_permissions=True)

	return {
		"submission": request_doc.name,
		"purchase_invoice": pi.name,
		"docstatus": pi.docstatus,
		"status": request_doc.status,
		"expected_total": request_doc.expected_total,
		"variance": request_doc.variance,
		"duplicate": False,
	}


def get_effective_supplier() -> str:
	_require_supplier_user()
	suppliers = sorted(set(get_parents_for_user("Supplier") or []))
	if not suppliers:
		frappe.throw(
			_("Su usuario no está asociado a un proveedor habilitado para el portal."),
			frappe.PermissionError,
		)
	if len(suppliers) != 1:
		frappe.throw(
			_("Su usuario tiene más de un proveedor asociado. Solicite regularizar el acceso."),
			frappe.PermissionError,
		)
	return suppliers[0]


def _require_supplier_user() -> str:
	user = str(getattr(frappe.session, "user", "") or "")
	if not user or user == "Guest":
		frappe.throw(_("Debe iniciar sesión."), frappe.PermissionError)

	user_type = frappe.db.get_value("User", user, "user_type")
	if user_type != "Website User" or "Supplier" not in set(frappe.get_roles(user) or []):
		frappe.throw(_("Se requiere un usuario de portal con rol Supplier."), frappe.PermissionError)
	return user


def _get_authorized_purchase_order(purchase_order: str, supplier: str):
	name = str(purchase_order or "").strip()
	if not name or len(name) > 140:
		frappe.throw(_("La Orden de Compra no está disponible."), frappe.PermissionError)

	po_state = frappe.db.get_value(
		"Purchase Order", name, ["supplier", "docstatus", "status"], as_dict=True
	)
	_assert_purchase_order_state(po_state, supplier)
	return frappe.get_doc("Purchase Order", name)


def _assert_purchase_order_state(po_state, supplier: str):
	if not po_state or po_state.supplier != supplier:
		frappe.throw(_("La Orden de Compra no está disponible."), frappe.PermissionError)
	if po_state.docstatus != 1 or po_state.status in {"Closed", "Cancelled"}:
		frappe.throw(_("La Orden de Compra debe estar enviada y abierta."))


def _lock_purchase_order(purchase_order: str):
	name = str(purchase_order or "").strip()
	if not name or len(name) > 140:
		frappe.throw(_("La Orden de Compra no está disponible."), frappe.PermissionError)

	purchase_order_table = frappe.qb.DocType("Purchase Order")
	locked = (
		frappe.qb.from_(purchase_order_table)
		.select(purchase_order_table.name)
		.where(purchase_order_table.name == name)
		.for_update()
	).run(pluck=True)
	if not locked:
		frappe.throw(_("La Orden de Compra no está disponible."), frappe.PermissionError)


def _get_authorized_purchase_receipt(purchase_receipt: str, supplier: str):
	name = str(purchase_receipt or "").strip()
	if not name or len(name) > 140:
		frappe.throw(_("La Recepción de Compra no está disponible."), frappe.PermissionError)

	pr_state = frappe.db.get_value(
		"Purchase Receipt",
		name,
		["supplier", "docstatus", "status", "is_return"],
		as_dict=True,
	)
	_assert_purchase_receipt_state(pr_state, supplier)
	return frappe.get_doc("Purchase Receipt", name)


def _assert_purchase_receipt_state(pr_state, supplier: str):
	if not pr_state or pr_state.supplier != supplier:
		frappe.throw(_("La Recepción de Compra no está disponible."), frappe.PermissionError)
	if pr_state.docstatus != 1 or pr_state.status in {"Closed", "Cancelled"}:
		frappe.throw(_("La Recepción de Compra debe estar enviada y abierta."))
	if pr_state.is_return:
		frappe.throw(_("Las devoluciones no pueden facturarse desde esta opción."))


def _lock_purchase_receipt(purchase_receipt: str):
	name = str(purchase_receipt or "").strip()
	if not name or len(name) > 140:
		frappe.throw(_("La Recepción de Compra no está disponible."), frappe.PermissionError)

	purchase_receipt_table = frappe.qb.DocType("Purchase Receipt")
	locked = (
		frappe.qb.from_(purchase_receipt_table)
		.select(purchase_receipt_table.name)
		.where(purchase_receipt_table.name == name)
		.for_update()
	).run(pluck=True)
	if not locked:
		frappe.throw(_("La Recepción de Compra no está disponible."), frappe.PermissionError)


def _get_item_availability(po) -> list[dict]:
	item_names = [row.name for row in po.items]
	billed_by_item = _get_submitted_billed_quantities(item_names)
	reserved_by_item = _get_reserved_quantities(po.name)
	result = []

	for row in po.items:
		billed_qty = flt(billed_by_item.get(row.name))
		reserved_qty = flt(reserved_by_item.get(row.name))
		available_qty = max(flt(row.qty) - billed_qty - reserved_qty, 0)
		result.append(
			{
				"purchase_order_item": row.name,
				"item_code": row.item_code,
				"description": row.description,
				"uom": row.uom,
				"currency": po.currency,
				"ordered_qty": flt(row.qty),
				"submitted_billed_qty": billed_qty,
				"reserved_qty": reserved_qty,
				"available_qty": available_qty,
				"qty": available_qty,
				"rate": flt(row.rate),
				"amount": flt(available_qty * flt(row.rate)),
			}
		)
	return result


def _get_submitted_billed_quantities(item_names: list[str]) -> dict[str, float]:
	if not item_names:
		return {}

	pi_item = frappe.qb.DocType("Purchase Invoice Item")
	rows = (
		frappe.qb.from_(pi_item)
		.select(pi_item.po_detail, Sum(pi_item.qty).as_("qty"))
		.where(pi_item.docstatus == 1)
		.where(pi_item.po_detail.isin(item_names))
		.groupby(pi_item.po_detail)
	).run(as_dict=True)
	return {row.po_detail: flt(row.qty) for row in rows}


def _get_reserved_quantities(purchase_order: str) -> dict[str, float]:
	active_submissions = frappe.get_all(
		SUBMISSION_DOCTYPE,
		filters={
			"purchase_order": purchase_order,
			"status": ["in", ACTIVE_RESERVATION_STATUSES],
		},
		pluck="name",
	)
	if not active_submissions:
		return {}

	rows = frappe.get_all(
		SUBMISSION_ITEM_DOCTYPE,
		filters={"parent": ["in", active_submissions]},
		fields=["purchase_order_item", "sum(qty) as qty"],
		group_by="purchase_order_item",
	)
	return {row.purchase_order_item: flt(row.qty) for row in rows}


def _get_purchase_receipt_item_availability(pr) -> list[dict]:
	invoiced_by_item = get_invoiced_qty_map(pr.name)
	returned_by_item = get_returned_qty_map(pr.name)
	reserved_by_item = _get_reserved_receipt_quantities(pr.name)
	bill_rejected = bool(
		frappe.db.get_single_value(
			"Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"
		)
	)
	result = []

	for row in pr.items:
		billable_qty = flt(row.received_qty if bill_rejected else row.qty)
		invoiced_qty = flt(invoiced_by_item.get(row.name))
		returned_qty = 0
		if not bill_rejected:
			returned_qty = max(flt(returned_by_item.get(row.name)) - flt(row.rejected_qty), 0)
		pending_qty = max(billable_qty - invoiced_qty - returned_qty, 0)
		reserved_qty = flt(reserved_by_item.get(row.name))
		available_qty = max(pending_qty - reserved_qty, 0)
		result.append(
			{
				"purchase_receipt_item": row.name,
				"item_code": row.item_code,
				"description": row.description,
				"uom": row.uom,
				"currency": pr.currency,
				"ordered_qty": billable_qty,
				"submitted_billed_qty": invoiced_qty,
				"returned_qty": returned_qty,
				"reserved_qty": reserved_qty,
				"available_qty": available_qty,
				"qty": available_qty,
				"rate": flt(row.rate),
				"amount": flt(available_qty * flt(row.rate)),
			}
		)
	return result


def _get_reserved_receipt_quantities(purchase_receipt: str) -> dict[str, float]:
	active_submissions = frappe.get_all(
		SUBMISSION_DOCTYPE,
		filters={
			"purchase_receipt": purchase_receipt,
			"status": ["in", ACTIVE_RESERVATION_STATUSES],
		},
		pluck="name",
	)
	if not active_submissions:
		return {}

	rows = frappe.get_all(
		SUBMISSION_ITEM_DOCTYPE,
		filters={"parent": ["in", active_submissions]},
		fields=["purchase_receipt_item", "sum(qty) as qty"],
		group_by="purchase_receipt_item",
	)
	return {row.purchase_receipt_item: flt(row.qty) for row in rows}


def _parse_requested_items(value) -> list[dict]:
	rows = frappe.parse_json(value) if isinstance(value, str) else value
	if not isinstance(rows, list) or not rows or len(rows) > MAX_ITEMS_PER_SUBMISSION:
		frappe.throw(_("Seleccione entre 1 y {0} ítems.").format(MAX_ITEMS_PER_SUBMISSION))

	parsed = []
	seen = set()
	for row in rows:
		if not isinstance(row, dict):
			frappe.throw(_("Los ítems enviados no tienen un formato válido."))
		po_detail = str(row.get("purchase_order_item") or "").strip()
		if not po_detail or len(po_detail) > 140 or po_detail in seen:
			frappe.throw(_("Los ítems enviados contienen referencias inválidas o repetidas."))
		seen.add(po_detail)
		qty = _positive_number(row.get("qty"), _("Cada cantidad debe ser mayor que cero."))
		parsed.append({"purchase_order_item": po_detail, "qty": qty})
	return parsed


def _parse_requested_receipt_items(value) -> list[dict]:
	rows = frappe.parse_json(value) if isinstance(value, str) else value
	if not isinstance(rows, list) or not rows or len(rows) > MAX_ITEMS_PER_SUBMISSION:
		frappe.throw(_("Seleccione entre 1 y {0} ítems.").format(MAX_ITEMS_PER_SUBMISSION))

	parsed = []
	seen = set()
	for row in rows:
		if not isinstance(row, dict):
			frappe.throw(_("Los ítems enviados no tienen un formato válido."))
		pr_detail = str(row.get("purchase_receipt_item") or "").strip()
		if not pr_detail or len(pr_detail) > 140 or pr_detail in seen:
			frappe.throw(_("Los ítems enviados contienen referencias inválidas o repetidas."))
		seen.add(pr_detail)
		qty = _positive_number(row.get("qty"), _("Cada cantidad debe ser mayor que cero."))
		parsed.append({"purchase_receipt_item": pr_detail, "qty": qty})
	return parsed


def _validate_requested_items(requested_items: list[dict], available_items: dict[str, dict]) -> list[dict]:
	validated = []
	for requested in requested_items:
		po_detail = requested["purchase_order_item"]
		available = available_items.get(po_detail)
		if not available:
			frappe.throw(_("Uno de los ítems no pertenece a la Orden de Compra."), frappe.PermissionError)

		qty = requested["qty"]
		if qty > flt(available["available_qty"]) + 1e-9:
			frappe.throw(
				_("La cantidad solicitada para el ítem {0} supera el saldo disponible.").format(
					available["item_code"]
				)
			)

		row = dict(available)
		row["qty"] = qty
		row["amount"] = flt(qty * flt(row["rate"]))
		validated.append(row)
	return validated


def _validate_requested_receipt_items(
	requested_items: list[dict], available_items: dict[str, dict]
) -> list[dict]:
	validated = []
	for requested in requested_items:
		pr_detail = requested["purchase_receipt_item"]
		available = available_items.get(pr_detail)
		if not available:
			frappe.throw(
				_("Uno de los ítems no pertenece a la Recepción de Compra."),
				frappe.PermissionError,
			)

		qty = requested["qty"]
		if qty > flt(available["available_qty"]) + 1e-9:
			frappe.throw(
				_("La cantidad solicitada para el ítem {0} supera el saldo recibido.").format(
					available["item_code"]
				)
			)

		row = dict(available)
		row["qty"] = qty
		row["amount"] = flt(qty * flt(row["rate"]))
		validated.append(row)
	return validated


def _make_purchase_invoice(po, bill_no: str, bill_date, items: list[dict], submission: str):
	quantities = {row["purchase_order_item"]: row["qty"] for row in items}
	pi = get_mapped_purchase_invoice(
		po.name,
		ignore_permissions=True,
		args={"filtered_children": list(quantities)},
	)
	mapped_items = {row.po_detail: row for row in pi.items}
	if set(mapped_items) != set(quantities):
		frappe.throw(_("ERPNext no pudo mapear todos los ítems seleccionados."))

	for po_detail, qty in quantities.items():
		mapped_items[po_detail].qty = qty

	pi.bill_no = bill_no
	pi.bill_date = bill_date
	pi.posting_date = nowdate()
	pi.remarks = _("Registrada desde el portal de proveedores: {0}").format(submission)
	_apply_purchase_invoice_fiscal_metadata(pi)
	pi.insert(ignore_permissions=True)
	return pi


def _make_purchase_invoice_from_receipt(
	pr, bill_no: str, bill_date, items: list[dict], submission: str
):
	quantities = {row["purchase_receipt_item"]: row["qty"] for row in items}
	pi = _map_purchase_receipt_to_invoice(pr.name, set(quantities))

	mapped_items = {row.pr_detail: row for row in pi.items}
	if set(mapped_items) != set(quantities):
		frappe.throw(_("ERPNext no pudo mapear todos los ítems recibidos seleccionados."))

	for pr_detail, qty in quantities.items():
		mapped_items[pr_detail].qty = qty

	pi.bill_no = bill_no
	pi.bill_date = bill_date
	pi.posting_date = nowdate()
	pi.remarks = _("Registrada desde una recepción en el portal de proveedores: {0}").format(
		submission
	)
	_apply_purchase_invoice_fiscal_metadata(pi)
	pi.insert(ignore_permissions=True)
	return pi


def _map_purchase_receipt_to_invoice(source_name: str, selected_items: set[str]):
	"""Use ERPNext v15's mapping rules with explicit server-side permission bypass."""
	returned_qty_map = get_returned_qty_map(source_name)
	invoiced_qty_map = get_invoiced_qty_map(source_name)
	bill_rejected = bool(
		frappe.db.get_single_value(
			"Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"
		)
	)

	def get_pending_qty(item_row):
		qty = item_row.received_qty if bill_rejected else item_row.qty
		pending_qty = flt(qty) - flt(invoiced_qty_map.get(item_row.name))
		if bill_rejected:
			return pending_qty, 0

		returned_qty = flt(returned_qty_map.get(item_row.name))
		if item_row.rejected_qty and returned_qty:
			returned_qty -= item_row.rejected_qty
		if returned_qty:
			if returned_qty >= pending_qty:
				pending_qty = 0
			else:
				pending_qty -= returned_qty
				returned_qty = 0
		return pending_qty, returned_qty

	def update_item(source, target, source_parent):
		target.qty, _returned_qty = get_pending_qty(source)
		if bill_rejected:
			target.rejected_qty = 0
		target.stock_qty = flt(target.qty) * flt(
			target.conversion_factor, target.precision("conversion_factor")
		)

	def set_missing_values(source, target):
		if not target.get("items"):
			frappe.throw(_("Todos los ítems ya fueron facturados o devueltos."))
		target.flags.ignore_permissions = True
		target.payment_terms_template = get_payment_terms_template(
			source.supplier, "Supplier", source.company
		)
		target.run_method("onload")
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")
		target.set_payment_schedule()

	return get_mapped_doc(
		"Purchase Receipt",
		source_name,
		{
			"Purchase Receipt": {
				"doctype": "Purchase Invoice",
				"field_map": {
					"supplier_warehouse": "supplier_warehouse",
					"is_return": "is_return",
					"bill_date": "bill_date",
				},
				"validation": {"docstatus": ["=", 1]},
			},
			"Purchase Receipt Item": {
				"doctype": "Purchase Invoice Item",
				"field_map": {
					"name": "pr_detail",
					"parent": "purchase_receipt",
					"qty": "received_qty",
					"purchase_order_item": "po_detail",
					"purchase_order": "purchase_order",
					"is_fixed_asset": "is_fixed_asset",
					"asset_location": "asset_location",
					"asset_category": "asset_category",
					"wip_composite_asset": "wip_composite_asset",
				},
				"postprocess": update_item,
				"filter": lambda item: get_pending_qty(item)[0] <= 0,
				"condition": lambda item: item.name in selected_items,
			},
			"Purchase Taxes and Charges": {
				"doctype": "Purchase Taxes and Charges",
				"reset_value": True,
			},
		},
		postprocess=set_missing_values,
		ignore_permissions=True,
	)


def _apply_purchase_invoice_fiscal_metadata(pi) -> None:
	"""Populate Ovenube fiscal fields only when its complete schema is installed."""
	invoice_meta = frappe.get_meta("Purchase Invoice")
	present_fields = {fieldname for fieldname in FISCAL_FIELDS if invoice_meta.get_field(fieldname)}
	if not present_fields:
		return
	if present_fields != FISCAL_FIELDS:
		frappe.throw(_("La configuración fiscal de Purchase Invoice está incompleta."))

	supplier_meta = frappe.get_meta("Supplier")
	if not all(
		supplier_meta.get_field(fieldname)
		for fieldname in ("nombre_tipo_documento", "codigo_tipo_documento")
	):
		frappe.throw(_("La configuración fiscal de Supplier está incompleta."))

	voucher = _get_fiscal_catalog_row(
		"Tipos de Comprobante",
		{"codigo_tipo_comprobante": FISCAL_INVOICE_CODE},
		"codigo_tipo_comprobante",
	)
	supplier_identity = frappe.db.get_value(
		"Supplier",
		pi.supplier,
		["nombre_tipo_documento", "codigo_tipo_documento"],
		as_dict=True,
	)
	if not supplier_identity:
		frappe.throw(_("No se encontró la identidad fiscal del proveedor."))

	identity_name = _clean_fiscal_value(supplier_identity.nombre_tipo_documento)
	identity_code = _clean_fiscal_value(supplier_identity.codigo_tipo_documento)
	identity_filters = identity_name or ({"codigo_tipo_documento": identity_code} if identity_code else None)
	if not identity_filters:
		frappe.throw(_("El proveedor no tiene configurado su tipo de documento fiscal."))

	identity = _get_fiscal_catalog_row(
		"Tipos de Documento de Identidad",
		identity_filters,
		"codigo_tipo_documento",
	)
	if identity_code and identity["code"] != identity_code:
		frappe.throw(_("El tipo y código de documento fiscal del proveedor no coinciden."))

	expected_values = {
		"tipo_comprobante": voucher["name"],
		"codigo_comprobante": voucher["code"],
		"tipo_documento_identidad": identity["name"],
		"codigo_tipo_documento": identity["code"],
	}
	for fieldname, expected in expected_values.items():
		current = _clean_fiscal_value(pi.get(fieldname))
		if current and current != expected:
			frappe.throw(_("El valor fiscal de {0} no coincide con el catálogo.").format(fieldname))
		pi.set(fieldname, expected)


def _get_fiscal_catalog_row(doctype: str, filters, code_field: str) -> dict[str, str]:
	if not frappe.db.exists("DocType", doctype):
		frappe.throw(_("Falta el catálogo fiscal {0}.").format(doctype))
	row = frappe.db.get_value(doctype, filters, ["name", code_field], as_dict=True)
	name = _clean_fiscal_value(getattr(row, "name", None))
	code = _clean_fiscal_value(getattr(row, code_field, None))
	if not name or not code:
		frappe.throw(_("El catálogo fiscal {0} no contiene un registro válido.").format(doctype))
	return {"name": name, "code": code}


def _clean_fiscal_value(value) -> str | None:
	if value in (None, ""):
		return None
	return " ".join(str(value).strip().split()) or None


def _decode_attachment(value, required_extension: str) -> tuple[str, bytes]:
	payload = frappe.parse_json(value) if isinstance(value, str) else value
	if not isinstance(payload, dict):
		frappe.throw(_("Adjunte los archivos PDF y XML requeridos."))

	original_name = str(payload.get("file_name") or "").strip().replace("\\", "/")
	file_name = PurePath(original_name).name
	encoded = str(payload.get("content") or "").strip()
	if not file_name or len(file_name) > 140 or not encoded:
		frappe.throw(_("El archivo adjunto no tiene un formato válido."))
	if not file_name.lower().endswith(required_extension):
		frappe.throw(_("El archivo {0} debe tener extensión {1}.").format(file_name, required_extension))

	if encoded.startswith("data:"):
		try:
			encoded = encoded.split(",", 1)[1]
		except IndexError:
			frappe.throw(_("El contenido del archivo {0} no es válido.").format(file_name))

	max_file_size = get_max_file_size()
	if len(encoded) > ((max_file_size + 2) // 3) * 4 + 1024:
		frappe.throw(_("El archivo {0} supera el tamaño máximo permitido.").format(file_name))

	try:
		content = base64.b64decode(encoded, validate=True)
	except (binascii.Error, ValueError):
		frappe.throw(_("El contenido del archivo {0} no es válido.").format(file_name))

	if not content or len(content) > max_file_size:
		frappe.throw(_("El archivo {0} está vacío o supera el tamaño permitido.").format(file_name))
	if required_extension == ".pdf" and not content.startswith(b"%PDF-"):
		frappe.throw(_("El archivo PDF no contiene una firma válida."))
	if required_extension == ".xml":
		try:
			xml_text = content.decode("utf-8-sig")
		except UnicodeDecodeError:
			frappe.throw(_("El archivo XML debe usar codificación UTF-8."))
		if not xml_text.lstrip().startswith("<"):
			frappe.throw(_("El archivo XML no contiene una estructura válida."))
	return file_name, content


def _validate_bill_date(value):
	if not value:
		frappe.throw(_("Ingrese la fecha de la factura."))
	value = getdate(value)
	if value > getdate(nowdate()):
		frappe.throw(_("La fecha de la factura no puede estar en el futuro."))
	return value


def _positive_number(value, message: str) -> float:
	number = flt(value)
	if not math.isfinite(number) or number <= 0:
		frappe.throw(message)
	return number


def _clean_remarks(value: str | None) -> str | None:
	remarks = " ".join(str(value or "").split()).strip()
	if len(remarks) > 500:
		frappe.throw(_("La observación no puede superar 500 caracteres."))
	return remarks or None


def _validate_purchase_invoice_duplicate(supplier: str, normalized_bill_no: str):
	purchase_invoice = frappe.qb.DocType("Purchase Invoice")
	normalized_existing_bill = Upper(Trim(purchase_invoice.bill_no))
	for whitespace in (" ", "\t", "\n", "\r"):
		normalized_existing_bill = Replace(normalized_existing_bill, whitespace, "")

	exists = (
		frappe.qb.from_(purchase_invoice)
		.select(purchase_invoice.name)
		.where(purchase_invoice.supplier == supplier)
		.where(purchase_invoice.docstatus < 2)
		.where(normalized_existing_bill == normalized_bill_no)
		.limit(1)
	).run(pluck=True)
	if exists:
		frappe.throw(_("La factura indicada ya está registrada para este proveedor."))


def _get_existing_submission(invoice_key: str):
	return frappe.db.get_value(
		SUBMISSION_DOCTYPE,
		{"supplier_invoice_key": invoice_key},
		["name", "purchase_invoice", "status", "expected_total", "variance"],
		as_dict=True,
	)


def _existing_submission_response(existing) -> dict:
	docstatus = None
	if existing.purchase_invoice:
		docstatus = frappe.db.get_value("Purchase Invoice", existing.purchase_invoice, "docstatus")
	return {
		"submission": existing.name,
		"purchase_invoice": existing.purchase_invoice,
		"docstatus": docstatus,
		"status": existing.status,
		"expected_total": existing.expected_total,
		"variance": existing.variance,
		"duplicate": True,
	}


def _pagination(limit_start, limit_page_length) -> tuple[int, int]:
	try:
		start = max(int(limit_start or 0), 0)
		length = int(limit_page_length or 20)
	except (TypeError, ValueError):
		frappe.throw(_("Los parámetros de paginación no son válidos."))
	return start, min(max(length, 1), 100)
