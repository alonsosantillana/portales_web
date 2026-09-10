# Copyright (c) 2026, Portales Web and contributors
# For license information, please see license.txt

import base64
import unittest
from unittest.mock import MagicMock, patch

import frappe

from portales_web import hooks
from portales_web.api import supplier_portal
from portales_web.portales_web.doctype.supplier_invoice_submission.supplier_invoice_submission import (
	make_supplier_invoice_key,
	normalize_bill_no,
)


class TestSupplierPortalSecurity(unittest.TestCase):
	def test_public_route_maps_to_the_protected_page(self):
		self.assertIn(
			{"from_route": "/registrar-factura", "to_route": "registrar_factura"},
			hooks.website_route_rules,
		)

	def test_bill_number_is_normalized_and_key_is_stable(self):
		self.assertEqual(normalize_bill_no(" f001 - 00015 "), "F001-00015")
		self.assertEqual(
			make_supplier_invoice_key("SUP-001", "F001-00015"),
			make_supplier_invoice_key("SUP-001", normalize_bill_no(" f001 - 00015 ")),
		)

	@patch.object(supplier_portal.frappe, "get_meta")
	def test_fiscal_adapter_is_noop_without_ovenube_schema(self, get_meta):
		get_meta.return_value.get_field.return_value = None
		invoice = MagicMock()

		supplier_portal._apply_purchase_invoice_fiscal_metadata(invoice)

		invoice.set.assert_not_called()

	@patch.object(supplier_portal, "get_parents_for_user", return_value=["SUP-001"])
	@patch.object(supplier_portal, "_require_supplier_user", return_value="supplier@example.com")
	def test_effective_supplier_uses_portal_user_relation(self, require_user, get_parents):
		self.assertEqual(supplier_portal.get_effective_supplier(), "SUP-001")
		require_user.assert_called_once_with()
		get_parents.assert_called_once_with("Supplier")

	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.PermissionError)
	@patch.object(supplier_portal, "get_parents_for_user", return_value=["SUP-001", "SUP-002"])
	@patch.object(supplier_portal, "_require_supplier_user", return_value="supplier@example.com")
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_multiple_suppliers_are_rejected(self, _require_user, _get_parents, _throw):
		with self.assertRaises(frappe.PermissionError):
			supplier_portal.get_effective_supplier()

	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.PermissionError)
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_purchase_order_from_another_supplier_is_rejected(self, _throw):
		with self.assertRaises(frappe.PermissionError):
			supplier_portal._assert_purchase_order_state(
				frappe._dict(
					{"supplier": "SUP-002", "docstatus": 1, "status": "To Receive and Bill"}
				),
				"SUP-001",
			)


class TestSupplierPortalQuantities(unittest.TestCase):
	def setUp(self):
		self.available = {
			"PO-ITEM-1": {
				"purchase_order_item": "PO-ITEM-1",
				"item_code": "ITEM-001",
				"description": "Item",
				"uom": "Unit",
				"currency": "PEN",
				"ordered_qty": 100,
				"submitted_billed_qty": 40,
				"reserved_qty": 30,
				"available_qty": 30,
				"qty": 30,
				"rate": 12.5,
				"amount": 375,
			}
		}

	def test_partial_quantity_uses_server_rate(self):
		rows = supplier_portal._validate_requested_items(
			[{"purchase_order_item": "PO-ITEM-1", "qty": 10, "rate": 0}],
			self.available,
		)
		self.assertEqual(rows[0]["qty"], 10)
		self.assertEqual(rows[0]["rate"], 12.5)
		self.assertEqual(rows[0]["amount"], 125)

	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.ValidationError)
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_quantity_over_available_is_rejected(self, _throw):
		with self.assertRaises(frappe.ValidationError):
			supplier_portal._validate_requested_items(
				[{"purchase_order_item": "PO-ITEM-1", "qty": 31}],
				self.available,
			)

	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.PermissionError)
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_item_from_another_purchase_order_is_rejected(self, _throw):
		with self.assertRaises(frappe.PermissionError):
			supplier_portal._validate_requested_items(
				[{"purchase_order_item": "PO-ITEM-OTHER", "qty": 1}],
				self.available,
			)


class TestSupplierPortalAttachments(unittest.TestCase):
	@patch.object(supplier_portal, "get_max_file_size", return_value=1024 * 1024)
	def test_pdf_signature_is_accepted(self, _max_size):
		content = b"%PDF-1.7\nportal test"
		name, decoded = supplier_portal._decode_attachment(
			{
				"file_name": "factura.pdf",
				"content": "data:application/pdf;base64," + base64.b64encode(content).decode(),
			},
			".pdf",
		)
		self.assertEqual(name, "factura.pdf")
		self.assertEqual(decoded, content)

	@patch.object(supplier_portal, "get_max_file_size", return_value=1024 * 1024)
	def test_utf8_xml_is_accepted(self, _max_size):
		content = b'<?xml version="1.0" encoding="UTF-8"?><Invoice />'
		name, decoded = supplier_portal._decode_attachment(
			{"file_name": "factura.xml", "content": base64.b64encode(content).decode()},
			".xml",
		)
		self.assertEqual(name, "factura.xml")
		self.assertEqual(decoded, content)

	@patch.object(supplier_portal, "get_max_file_size", return_value=1024 * 1024)
	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.ValidationError)
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_renamed_non_pdf_is_rejected(self, _throw, _max_size):
		with self.assertRaises(frappe.ValidationError):
			supplier_portal._decode_attachment(
				{
					"file_name": "factura.pdf",
					"content": base64.b64encode(b"not a pdf").decode(),
				},
				".pdf",
			)

	@patch.object(supplier_portal, "get_max_file_size", return_value=8)
	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.ValidationError)
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_oversized_file_is_rejected(self, _throw, _max_size):
		with self.assertRaises(frappe.ValidationError):
			supplier_portal._decode_attachment(
				{
					"file_name": "factura.pdf",
					"content": base64.b64encode(b"%PDF-too-large").decode(),
				},
				".pdf",
			)


if __name__ == "__main__":
	unittest.main()
