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
		self.assertIn(
			{
				"from_route": "/registrar-factura-recepcion",
				"to_route": "registrar_factura_recepcion",
			},
			hooks.website_route_rules,
		)
		self.assertIn(
			{
				"title": "Facturar recepción",
				"route": "/registrar-factura-recepcion",
				"role": "Supplier",
			},
			hooks.portal_menu_items,
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

	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.PermissionError)
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_purchase_receipt_from_another_supplier_is_rejected(self, _throw):
		with self.assertRaises(frappe.PermissionError):
			supplier_portal._assert_purchase_receipt_state(
				frappe._dict(
					{"supplier": "SUP-002", "docstatus": 1, "status": "To Bill", "is_return": 0}
				),
				"SUP-001",
			)

	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.ValidationError)
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_purchase_receipt_return_is_rejected(self, _throw):
		with self.assertRaises(frappe.ValidationError):
			supplier_portal._assert_purchase_receipt_state(
				frappe._dict(
					{"supplier": "SUP-001", "docstatus": 1, "status": "To Bill", "is_return": 1}
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

	@patch.object(supplier_portal, "_get_reserved_receipt_quantities", return_value={"PR-ITEM-1": 1})
	@patch.object(supplier_portal, "get_returned_qty_map", return_value={"PR-ITEM-1": 3})
	@patch.object(supplier_portal, "get_invoiced_qty_map", return_value={"PR-ITEM-1": 2})
	@patch.object(supplier_portal.frappe.db, "get_single_value", return_value=0)
	def test_receipt_availability_deducts_invoices_returns_and_reservations(
		self, _setting, _invoiced, _returned, _reserved
	):
		receipt = MagicMock()
		receipt.name = "PR-001"
		receipt.currency = "PEN"
		receipt.items = [
			frappe._dict(
				{
					"name": "PR-ITEM-1",
					"item_code": "ITEM-001",
					"description": "Item",
					"uom": "Unit",
					"qty": 10,
					"received_qty": 12,
					"rejected_qty": 1,
					"rate": 12.5,
				}
			)
		]

		row = supplier_portal._get_purchase_receipt_item_availability(receipt)[0]

		self.assertEqual(row["returned_qty"], 2)
		self.assertEqual(row["available_qty"], 5)

	@patch.object(supplier_portal, "_get_reserved_receipt_quantities", return_value={"PR-ITEM-1": 1})
	@patch.object(supplier_portal, "get_returned_qty_map", return_value={"PR-ITEM-1": 3})
	@patch.object(supplier_portal, "get_invoiced_qty_map", return_value={"PR-ITEM-1": 2})
	@patch.object(supplier_portal.frappe.db, "get_single_value", return_value=1)
	def test_receipt_availability_can_bill_rejected_quantity(
		self, _setting, _invoiced, _returned, _reserved
	):
		receipt = MagicMock()
		receipt.name = "PR-001"
		receipt.currency = "PEN"
		receipt.items = [
			frappe._dict(
				{
					"name": "PR-ITEM-1",
					"item_code": "ITEM-001",
					"description": "Item",
					"uom": "Unit",
					"qty": 10,
					"received_qty": 12,
					"rejected_qty": 2,
					"rate": 12.5,
				}
			)
		]

		row = supplier_portal._get_purchase_receipt_item_availability(receipt)[0]

		self.assertEqual(row["ordered_qty"], 12)
		self.assertEqual(row["returned_qty"], 0)
		self.assertEqual(row["available_qty"], 9)

	def test_partial_receipt_quantity_uses_server_rate(self):
		available = {
			"PR-ITEM-1": {
				"purchase_receipt_item": "PR-ITEM-1",
				"item_code": "ITEM-001",
				"description": "Item",
				"uom": "Unit",
				"currency": "PEN",
				"ordered_qty": 10,
				"submitted_billed_qty": 2,
				"returned_qty": 1,
				"reserved_qty": 1,
				"available_qty": 6,
				"qty": 6,
				"rate": 15,
				"amount": 90,
			}
		}

		rows = supplier_portal._validate_requested_receipt_items(
			[{"purchase_receipt_item": "PR-ITEM-1", "qty": 4, "rate": 0}], available
		)

		self.assertEqual(rows[0]["qty"], 4)
		self.assertEqual(rows[0]["rate"], 15)
		self.assertEqual(rows[0]["amount"], 60)

	@patch.object(supplier_portal.frappe, "throw", side_effect=frappe.PermissionError)
	@patch.object(supplier_portal, "_", new=lambda value: value)
	def test_item_from_another_purchase_receipt_is_rejected(self, _throw):
		with self.assertRaises(frappe.PermissionError):
			supplier_portal._validate_requested_receipt_items(
				[{"purchase_receipt_item": "PR-ITEM-OTHER", "qty": 1}], {}
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


class TestSupplierReceiptMapper(unittest.TestCase):
	@patch.object(supplier_portal, "_apply_purchase_invoice_fiscal_metadata")
	@patch.object(supplier_portal, "_map_purchase_receipt_to_invoice")
	def test_mapper_keeps_native_references(self, native_mapper, fiscal_adapter):
		invoice_item = frappe._dict(
			{
				"pr_detail": "PR-ITEM-1",
				"purchase_receipt": "PR-001",
				"qty": 5,
			}
		)
		invoice = MagicMock()
		invoice.items = [invoice_item]
		native_mapper.return_value = invoice
		receipt = MagicMock()
		receipt.name = "PR-001"

		result = supplier_portal._make_purchase_invoice_from_receipt(
			receipt,
			"F001-1",
			"2026-09-10",
			[{"purchase_receipt_item": "PR-ITEM-1", "qty": 2}],
			"SIS-1",
		)

		self.assertIs(result, invoice)
		self.assertEqual(invoice_item.qty, 2)
		self.assertEqual(invoice_item.purchase_receipt, "PR-001")
		native_mapper.assert_called_once_with("PR-001", {"PR-ITEM-1"})
		fiscal_adapter.assert_called_once_with(invoice)
		invoice.insert.assert_called_once_with(ignore_permissions=True)

	@patch.object(supplier_portal.frappe.db, "get_single_value", return_value=0)
	@patch.object(supplier_portal, "get_invoiced_qty_map", return_value={})
	@patch.object(supplier_portal, "get_returned_qty_map", return_value={})
	@patch.object(supplier_portal, "get_mapped_doc")
	def test_receipt_adapter_bypasses_permissions_only_in_mapping_engine(
		self, mapped_doc, _returned, _invoiced, _setting
	):
		invoice = MagicMock()
		mapped_doc.return_value = invoice

		result = supplier_portal._map_purchase_receipt_to_invoice(
			"PR-001", {"PR-ITEM-1"}
		)

		self.assertIs(result, invoice)
		self.assertTrue(mapped_doc.call_args.kwargs["ignore_permissions"])
		mapping = mapped_doc.call_args.args[2]
		self.assertEqual(
			mapping["Purchase Receipt Item"]["field_map"]["name"], "pr_detail"
		)
		self.assertEqual(
			mapping["Purchase Receipt Item"]["field_map"]["parent"],
			"purchase_receipt",
		)

if __name__ == "__main__":
	unittest.main()
