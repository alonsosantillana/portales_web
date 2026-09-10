frappe.ready(() => {
	const api = "portales_web.api.supplier_portal";
	const form = document.getElementById("supplier-invoice-form");
	const purchaseOrder = document.getElementById("purchase-order");
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

	const clearItems = (message = __("Seleccione una Orden de Compra.")) => {
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
			clearItems(__("La Orden de Compra no tiene cantidades disponibles."));
			return;
		}

		for (const item of rows) {
			const row = itemsBody.insertRow();
			row.dataset.purchaseOrderItem = item.purchase_order_item;
			addTextCell(row, item.item_code);
			addTextCell(row, item.description);
			addTextCell(row, formatNumber(item.ordered_qty), "text-right");
			addTextCell(row, formatNumber(item.submitted_billed_qty), "text-right");
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

	const loadPurchaseOrders = async () => {
		try {
			const response = await call("get_eligible_purchase_orders");
			const orders = response.message || [];
			purchaseOrder.replaceChildren();
			const empty = document.createElement("option");
			empty.value = "";
			empty.textContent = orders.length
				? __("Seleccione una Orden de Compra")
				: __("No hay Órdenes de Compra disponibles");
			purchaseOrder.appendChild(empty);
			for (const order of orders) {
				const option = document.createElement("option");
				option.value = order.name;
				option.textContent = `${order.name} · ${order.currency} ${formatNumber(
					order.grand_total
				)}`;
				purchaseOrder.appendChild(option);
			}
			purchaseOrder.disabled = !orders.length;
		} catch (error) {
			purchaseOrder.replaceChildren();
			const option = document.createElement("option");
			option.textContent = __("No fue posible cargar las órdenes");
			purchaseOrder.appendChild(option);
			purchaseOrder.disabled = true;
		}
	};

	const loadItems = async () => {
		const name = purchaseOrder.value;
		if (!name) {
			clearItems();
			return;
		}
		clearItems(__("Cargando ítems..."));
		try {
			const response = await call("get_purchase_order_items", { purchase_order: name });
			renderItems(response.message || {});
		} catch (error) {
			clearItems(__("No fue posible cargar los ítems de la orden."));
		}
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
				const poCell = addTextCell(row, "");
				const poLink = document.createElement("a");
				poLink.href = `/purchase-orders/${encodeURIComponent(submission.purchase_order)}`;
				poLink.textContent = submission.purchase_order;
				poCell.appendChild(poLink);
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
				rows.push({ purchase_order_item: row.dataset.purchaseOrderItem, qty });
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
			const response = await call("submit_invoice", {
				purchase_order: purchaseOrder.value,
				bill_no: document.getElementById("bill-no").value,
				bill_date: document.getElementById("bill-date").value,
				declared_total: document.getElementById("declared-total").value,
				items: JSON.stringify(items),
				invoice_pdf: JSON.stringify(invoicePdf),
				invoice_xml: JSON.stringify(invoiceXml),
				supplier_remarks: document.getElementById("supplier-remarks").value,
			});
			const result = response.message || {};
			frappe.msgprint({
				title: result.duplicate ? __("Factura ya registrada") : __("Factura registrada"),
				message: __("Registro {0}. Purchase Invoice {1} en borrador.", [
					result.submission,
					result.purchase_invoice,
				]),
				indicator: result.duplicate ? "orange" : "green",
			});
			if (!result.duplicate) form.reset();
			clearItems();
			await Promise.all([loadPurchaseOrders(), loadSubmissions()]);
		} finally {
			submitButton.disabled = false;
		}
	};

	purchaseOrder.addEventListener("change", loadItems);
	form.addEventListener("submit", handleSubmit);
	document.getElementById("bill-date").max = frappe.datetime.get_today();
	Promise.all([loadPurchaseOrders(), loadSubmissions()]);
});
