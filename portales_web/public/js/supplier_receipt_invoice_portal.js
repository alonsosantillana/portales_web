frappe.ready(() => {
	const api = "portales_web.api.supplier_portal";
	const form = document.getElementById("supplier-receipt-invoice-form");
	const purchaseReceipt = document.getElementById("purchase-receipt");
	const currency = document.getElementById("currency");
	const itemsBody = document.getElementById("items-body");
	const itemsWrapper = document.getElementById("items-wrapper");
	const itemsEmpty = document.getElementById("items-empty");
	const submissionsBody = document.getElementById("submissions-body");
	const submissionsWrapper = document.getElementById("submissions-wrapper");
	const submissionsEmpty = document.getElementById("submissions-empty");
	const submitButton = document.getElementById("submit-invoice");

	const call = (method, args = {}) =>
		frappe.call({
			method: `${api}.${method}`,
			args,
		});

	const addTextCell = (row, value, className = "") => {
		const cell = row.insertCell();
		cell.textContent = value ?? "";
		if (className) cell.className = className;
		return cell;
	};

	const formatNumber = (value) => {
		const number = Number(value || 0);
		return Number.isFinite(number)
			? number.toLocaleString(undefined, { maximumFractionDigits: 6 })
			: "0";
	};

	const readFile = (file) =>
		new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve({ file_name: file.name, content: reader.result });
			reader.onerror = () =>
				reject(new Error(__("No se pudo leer el archivo {0}.", [file.name])));
			reader.readAsDataURL(file);
		});

	const clearItems = (message = __("Seleccione una Recepción de Compra.")) => {
		itemsBody.replaceChildren();
		itemsWrapper.classList.add("d-none");
		itemsEmpty.classList.remove("d-none");
		itemsEmpty.textContent = message;
		currency.value = "";
	};

	const renderItems = (data) => {
		itemsBody.replaceChildren();
		currency.value = data.currency || "";
		const rows = data.items || [];
		if (!rows.length) {
			clearItems(__("La Recepción de Compra no tiene cantidades disponibles."));
			return;
		}

		for (const item of rows) {
			const row = itemsBody.insertRow();
			row.dataset.purchaseReceiptItem = item.purchase_receipt_item;
			addTextCell(row, item.item_code);
			addTextCell(row, item.description);
			addTextCell(row, formatNumber(item.ordered_qty), "text-right");
			addTextCell(row, formatNumber(item.submitted_billed_qty), "text-right");
			addTextCell(row, formatNumber(item.returned_qty), "text-right");
			addTextCell(row, formatNumber(item.reserved_qty), "text-right");
			addTextCell(row, formatNumber(item.available_qty), "text-right");
			const inputCell = row.insertCell();
			const input = document.createElement("input");
			input.type = "number";
			input.className = "form-control qty-input";
			input.min = "0";
			input.max = String(item.available_qty);
			input.step = "any";
			input.value = String(item.available_qty);
			input.dataset.availableQty = String(item.available_qty);
			inputCell.appendChild(input);
		}

		itemsEmpty.classList.add("d-none");
		itemsWrapper.classList.remove("d-none");
	};

	const loadPurchaseReceipts = async () => {
		try {
			const response = await call("get_eligible_purchase_receipts");
			const receipts = response.message || [];
			purchaseReceipt.replaceChildren();
			const empty = document.createElement("option");
			empty.value = "";
			empty.textContent = receipts.length
				? __("Seleccione una Recepción de Compra")
				: __("No hay Recepciones de Compra disponibles");
			purchaseReceipt.appendChild(empty);
			for (const receipt of receipts) {
				const option = document.createElement("option");
				option.value = receipt.name;
				option.textContent = `${receipt.name} · ${receipt.currency} ${formatNumber(
					receipt.grand_total
				)}`;
				purchaseReceipt.appendChild(option);
			}
			purchaseReceipt.disabled = !receipts.length;
		} catch (error) {
			purchaseReceipt.replaceChildren();
			const option = document.createElement("option");
			option.textContent = __("No fue posible cargar las recepciones");
			purchaseReceipt.appendChild(option);
			purchaseReceipt.disabled = true;
		}
	};

	const loadItems = async () => {
		const name = purchaseReceipt.value;
		if (!name) {
			clearItems();
			return;
		}
		clearItems(__("Cargando ítems..."));
		try {
			const response = await call("get_purchase_receipt_items", {
				purchase_receipt: name,
			});
			renderItems(response.message || {});
		} catch (error) {
			clearItems(__("No fue posible cargar los ítems de la recepción."));
		}
	};

	const addSourceCell = (row, submission) => {
		const cell = addTextCell(row, "");
		const isReceipt = submission.source_type === "Purchase Receipt";
		const label = `${isReceipt ? __("Recepción") : __("Orden")} · ${submission.source_name}`;
		if (isReceipt) {
			cell.textContent = label;
			return;
		}
		const link = document.createElement("a");
		link.href = `/purchase-orders/${encodeURIComponent(submission.source_name)}`;
		link.textContent = label;
		cell.appendChild(link);
	};

	const loadSubmissions = async () => {
		try {
			const response = await call("get_my_submissions");
			const submissions = response.message || [];
			submissionsBody.replaceChildren();
			if (!submissions.length) {
				submissionsEmpty.textContent = __("Todavía no hay facturas registradas.");
				submissionsEmpty.classList.remove("d-none");
				submissionsWrapper.classList.add("d-none");
				return;
			}

			for (const submission of submissions) {
				const row = submissionsBody.insertRow();
				addTextCell(row, submission.name);
				addTextCell(row, submission.bill_no);
				addSourceCell(row, submission);
				addTextCell(row, submission.status);
				const piCell = addTextCell(row, "");
				if (submission.purchase_invoice) {
					const piLink = document.createElement("a");
					piLink.href = `/purchase-invoices/${encodeURIComponent(
						submission.purchase_invoice
					)}`;
					piLink.textContent = submission.purchase_invoice;
					piCell.appendChild(piLink);
				} else {
					piCell.textContent = "—";
				}
			}
			submissionsEmpty.classList.add("d-none");
			submissionsWrapper.classList.remove("d-none");
		} catch (error) {
			submissionsEmpty.textContent = __("No fue posible cargar los registros.");
		}
	};

	const collectItems = () => {
		const rows = [];
		for (const row of itemsBody.rows) {
			const input = row.querySelector(".qty-input");
			const qty = Number(input.value);
			if (Number.isFinite(qty) && qty > 0) {
				rows.push({ purchase_receipt_item: row.dataset.purchaseReceiptItem, qty });
			}
		}
		return rows;
	};

	const handleSubmit = async (event) => {
		event.preventDefault();
		if (!form.reportValidity()) return;

		const items = collectItems();
		if (!items.length) {
			frappe.msgprint(__("Ingrese al menos una cantidad mayor que cero."));
			return;
		}

		const pdf = document.getElementById("invoice-pdf").files[0];
		const xml = document.getElementById("invoice-xml").files[0];
		if (!pdf || !xml) {
			frappe.msgprint(__("Adjunte el PDF y el XML de la factura."));
			return;
		}

		submitButton.disabled = true;
		try {
			const [invoicePdf, invoiceXml] = await Promise.all([readFile(pdf), readFile(xml)]);
			const response = await call("submit_invoice_from_receipt", {
				purchase_receipt: purchaseReceipt.value,
				bill_no: document.getElementById("bill-no").value,
				bill_date: document.getElementById("bill-date").value,
				declared_total: document.getElementById("declared-total").value,
				items: JSON.stringify(items),
				invoice_pdf: JSON.stringify(invoicePdf),
				invoice_xml: JSON.stringify(invoiceXml),
				supplier_remarks: document.getElementById("supplier-remarks").value,
			});
			const result = response.message || {};
			const resultMessage = result.purchase_invoice
				? __("Registro {0}. Purchase Invoice {1} en borrador.", [
						result.submission,
						result.purchase_invoice,
					])
				: __("Registro {0} en estado {1}, sin Factura de Compra vinculada.", [
						result.submission,
						result.status,
					]);
			frappe.msgprint({
				title: result.duplicate ? __("Factura ya registrada") : __("Factura registrada"),
				message: resultMessage,
				indicator: result.duplicate ? "orange" : "green",
			});
			if (!result.duplicate) form.reset();
			clearItems();
			await Promise.all([loadPurchaseReceipts(), loadSubmissions()]);
		} finally {
			submitButton.disabled = false;
		}
	};

	purchaseReceipt.addEventListener("change", loadItems);
	form.addEventListener("submit", handleSubmit);
	document.getElementById("bill-date").max = frappe.datetime.get_today();
	Promise.all([loadPurchaseReceipts(), loadSubmissions()]);
});
