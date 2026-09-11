# Copyright (c) 2026, Portales Web and contributors
# For license information, please see license.txt

import base64
from io import BytesIO

import frappe
from erpnext.accounts.party import get_party_account
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate
from pypdf import PdfWriter

from portales_web.api.supplier_portal import (
	_lock_purchase_order,
	_lock_purchase_receipt,
	get_purchase_order_items,
	get_purchase_receipt_items,
	submit_invoice,
	submit_invoice_from_receipt,
)


class TestSupplierPortalIntegration(FrappeTestCase):
	def test_purchase_order_lock_serializes_concurrent_requests(self):
		purchase_orders = frappe.get_all("Purchase Order", pluck="name", limit=1)
		if not purchase_orders:
			self.skipTest("A Purchase Order is required to verify row locking")

		_lock_purchase_order(purchase_orders[0])
		with self.secondary_connection():
			frappe.db.sql("SET SESSION innodb_lock_wait_timeout = 1")
			with self.assertRaises(frappe.QueryTimeoutError) as timeout:
				_lock_purchase_order(purchase_orders[0])
				self.assertEqual(timeout.exception.__cause__.args[0], 1205)

	def test_purchase_receipt_lock_serializes_concurrent_requests(self):
		purchase_receipts = frappe.get_all("Purchase Receipt", pluck="name", limit=1)
		if not purchase_receipts:
			self.skipTest("A Purchase Receipt is required to verify row locking")

		_lock_purchase_receipt(purchase_receipts[0])
		with self.secondary_connection():
			frappe.db.sql("SET SESSION innodb_lock_wait_timeout = 1")
			with self.assertRaises(frappe.QueryTimeoutError) as timeout:
				_lock_purchase_receipt(purchase_receipts[0])
			self.assertEqual(timeout.exception.__cause__.args[0], 1205)

	def test_submission_creates_private_draft_and_reserves_quantity(self):
		original_user = frappe.session.user
		file_urls = []
		try:
			frappe.set_user("Administrator")
			company = frappe.get_all("Company", pluck="name", order_by="creation asc", limit=1)[0]
			company_currency = frappe.get_cached_value("Company", company, "default_currency")
			supplier = None
			for supplier_name in frappe.get_all(
				"Supplier", filters={"disabled": 0}, pluck="name", order_by="creation asc", limit=500
			):
				account = get_party_account("Supplier", supplier_name, company)
				if frappe.get_cached_value("Account", account, "account_currency") == company_currency:
					supplier = frappe.get_doc("Supplier", supplier_name)
					break
			self.assertIsNotNone(supplier, "A Supplier in the company currency is required for this test")
			item = frappe.get_doc(
				"Item",
				frappe.get_all(
					"Item",
					filters={"disabled": 0, "is_purchase_item": 1, "is_stock_item": 0},
					pluck="name",
					order_by="creation asc",
					limit=1,
				)[0],
			)
			uom = item.stock_uom
			suffix = frappe.generate_hash(length=10)
			pdf_buffer = BytesIO()
			pdf_writer = PdfWriter()
			pdf_writer.add_blank_page(width=72, height=72)
			pdf_writer.write(pdf_buffer)
			pdf_content = base64.b64encode(pdf_buffer.getvalue()).decode()

			user_email = f"portal-test-{suffix}@example.com"
			frappe.get_doc(
				{
					"doctype": "User",
					"email": user_email,
					"first_name": "Portal Test Supplier",
					"user_type": "Website User",
					"send_welcome_email": 0,
					"roles": [{"role": "Supplier"}],
				}
			).insert(ignore_permissions=True)
			supplier.append("portal_users", {"user": user_email})
			supplier.save()

			purchase_order = frappe.get_doc(
				{
					"doctype": "Purchase Order",
					"company": company,
					"supplier": supplier.name,
					"currency": company_currency,
					"conversion_rate": 1,
					"price_list_currency": company_currency,
					"plc_conversion_rate": 1,
					"transaction_date": nowdate(),
					"schedule_date": add_days(nowdate(), 1),
					"items": [
						{
							"item_code": item.name,
							"item_name": item.item_name,
							"description": item.item_name,
							"uom": uom,
							"stock_uom": uom,
							"conversion_factor": 1,
							"qty": 5,
							"rate": 10,
							"schedule_date": add_days(nowdate(), 1),
						}
					],
				}
			)
			purchase_order.set_missing_values()
			purchase_order.insert()
			purchase_order.submit()

			frappe.set_user(user_email)
			result = submit_invoice(
				purchase_order=purchase_order.name,
				bill_no=f" f001 - {suffix} ",
				bill_date=nowdate(),
				declared_total=20,
				items=[{"purchase_order_item": purchase_order.items[0].name, "qty": 2}],
				invoice_pdf={
					"file_name": f"invoice-{suffix}.pdf",
					"content": pdf_content,
				},
				invoice_xml={
					"file_name": f"invoice-{suffix}.xml",
					"content": base64.b64encode(b'<?xml version="1.0"?><Invoice />').decode(),
				},
			)

			submission = frappe.get_doc("Supplier Invoice Submission", result["submission"])
			purchase_invoice = frappe.get_doc("Purchase Invoice", result["purchase_invoice"])
			file_urls.extend([submission.invoice_pdf, submission.invoice_xml])

			self.assertEqual(result["docstatus"], 0)
			self.assertEqual(submission.status, "En revisión")
			self.assertEqual(submission.supplier, supplier.name)
			self.assertEqual(purchase_invoice.docstatus, 0)
			self.assertEqual(purchase_invoice.items[0].purchase_order, purchase_order.name)
			self.assertEqual(purchase_invoice.items[0].qty, 2)
			self.assertEqual(purchase_invoice.codigo_comprobante, "01")
			self.assertEqual(purchase_invoice.codigo_tipo_documento, supplier.codigo_tipo_documento)
			self.assertTrue(all(url.startswith("/private/files/") for url in file_urls))
			self.assertTrue(
				all(frappe.db.get_value("File", {"file_url": url}, "is_private") for url in file_urls)
			)

			availability = get_purchase_order_items(purchase_order.name)
			self.assertEqual(availability["items"][0]["reserved_qty"], 2)
			self.assertEqual(availability["items"][0]["available_qty"], 3)

			duplicate = submit_invoice(
				purchase_order=purchase_order.name,
				bill_no=f"F001-{suffix}",
				bill_date=nowdate(),
				declared_total=20,
				items=[{"purchase_order_item": purchase_order.items[0].name, "qty": 2}],
				invoice_pdf={
					"file_name": f"invoice-{suffix}.pdf",
					"content": pdf_content,
				},
				invoice_xml={
					"file_name": f"invoice-{suffix}.xml",
					"content": base64.b64encode(b'<?xml version="1.0"?><Invoice />').decode(),
				},
			)
			self.assertTrue(duplicate["duplicate"])
			self.assertEqual(duplicate["purchase_invoice"], purchase_invoice.name)

			frappe.set_user("Administrator")
			purchase_invoice.submit()
			submission.reload()
			self.assertEqual(submission.status, "Procesada")

			purchase_invoice.cancel()
			submission.reload()
			self.assertEqual(submission.status, "Rechazada")
		finally:
			frappe.set_user("Administrator")
			for file_url in file_urls:
				file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
				if file_name:
					frappe.delete_doc("File", file_name, ignore_permissions=True, force=True)
			frappe.set_user(original_user)

	def test_receipt_submission_creates_native_private_draft_and_reserves_quantity(self):
		original_user = frappe.session.user
		file_urls = []
		try:
			frappe.set_user("Administrator")
			company = frappe.get_all("Company", pluck="name", order_by="creation asc", limit=1)[0]
			company_currency = frappe.get_cached_value("Company", company, "default_currency")
			supplier = None
			for supplier_name in frappe.get_all(
				"Supplier", filters={"disabled": 0}, pluck="name", order_by="creation asc", limit=500
			):
				account = get_party_account("Supplier", supplier_name, company)
				if frappe.get_cached_value("Account", account, "account_currency") == company_currency:
					supplier = frappe.get_doc("Supplier", supplier_name)
					break
			self.assertIsNotNone(supplier, "A Supplier in the company currency is required for this test")
			item = frappe.get_doc(
				"Item",
				frappe.get_all(
					"Item",
					filters={"disabled": 0, "is_purchase_item": 1, "is_stock_item": 0},
					pluck="name",
					order_by="creation asc",
					limit=1,
				)[0],
			)
			suffix = frappe.generate_hash(length=10)
			pdf_buffer = BytesIO()
			pdf_writer = PdfWriter()
			pdf_writer.add_blank_page(width=72, height=72)
			pdf_writer.write(pdf_buffer)
			pdf_content = base64.b64encode(pdf_buffer.getvalue()).decode()

			user_email = f"portal-receipt-test-{suffix}@example.com"
			frappe.get_doc(
				{
					"doctype": "User",
					"email": user_email,
					"first_name": "Portal Receipt Test Supplier",
					"user_type": "Website User",
					"send_welcome_email": 0,
					"roles": [{"role": "Supplier"}],
				}
			).insert(ignore_permissions=True)
			supplier.append("portal_users", {"user": user_email})
			supplier.save()

			purchase_order = frappe.get_doc(
				{
					"doctype": "Purchase Order",
					"company": company,
					"supplier": supplier.name,
					"currency": company_currency,
					"conversion_rate": 1,
					"price_list_currency": company_currency,
					"plc_conversion_rate": 1,
					"transaction_date": nowdate(),
					"schedule_date": add_days(nowdate(), 1),
					"items": [
						{
							"item_code": item.name,
							"item_name": item.item_name,
							"description": item.item_name,
							"uom": item.stock_uom,
							"stock_uom": item.stock_uom,
							"conversion_factor": 1,
							"qty": 5,
							"rate": 10,
							"schedule_date": add_days(nowdate(), 1),
						}
					],
				}
			)
			purchase_order.set_missing_values()
			purchase_order.insert()
			purchase_order.submit()

			purchase_receipt = make_purchase_receipt(purchase_order.name)
			purchase_receipt.insert()
			purchase_receipt.submit()

			frappe.set_user(user_email)
			result = submit_invoice_from_receipt(
				purchase_receipt=purchase_receipt.name,
				bill_no=f" r001 - {suffix} ",
				bill_date=nowdate(),
				declared_total=20,
				items=[
					{"purchase_receipt_item": purchase_receipt.items[0].name, "qty": 2}
				],
				invoice_pdf={
					"file_name": f"receipt-invoice-{suffix}.pdf",
					"content": pdf_content,
				},
				invoice_xml={
					"file_name": f"receipt-invoice-{suffix}.xml",
					"content": base64.b64encode(b'<?xml version="1.0"?><Invoice />').decode(),
				},
			)

			submission = frappe.get_doc("Supplier Invoice Submission", result["submission"])
			purchase_invoice = frappe.get_doc("Purchase Invoice", result["purchase_invoice"])
			file_urls.extend([submission.invoice_pdf, submission.invoice_xml])

			self.assertEqual(result["docstatus"], 0)
			self.assertEqual(submission.source_type, "Purchase Receipt")
			self.assertEqual(submission.purchase_receipt, purchase_receipt.name)
			self.assertFalse(submission.purchase_order)
			self.assertEqual(submission.items[0].purchase_receipt_item, purchase_receipt.items[0].name)
			self.assertEqual(purchase_invoice.docstatus, 0)
			self.assertEqual(purchase_invoice.items[0].purchase_receipt, purchase_receipt.name)
			self.assertEqual(purchase_invoice.items[0].pr_detail, purchase_receipt.items[0].name)
			self.assertEqual(purchase_invoice.items[0].purchase_order, purchase_order.name)
			self.assertEqual(purchase_invoice.items[0].qty, 2)
			self.assertTrue(all(url.startswith("/private/files/") for url in file_urls))

			availability = get_purchase_receipt_items(purchase_receipt.name)
			self.assertEqual(availability["items"][0]["reserved_qty"], 2)
			self.assertEqual(availability["items"][0]["available_qty"], 3)

			frappe.set_user("Administrator")
			purchase_invoice.submit()
			submission.reload()
			self.assertEqual(submission.status, "Procesada")

			purchase_invoice.cancel()
			submission.reload()
			self.assertEqual(submission.status, "Rechazada")
		finally:
			frappe.set_user("Administrator")
			for file_url in file_urls:
				file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
				if file_name:
					frappe.delete_doc("File", file_name, ignore_permissions=True, force=True)
			frappe.set_user(original_user)
