## Context

ERPNext v15 implementa `make_purchase_invoice` en el controlador de Purchase Receipt. El mapeador calcula cantidades pendientes considerando facturas enviadas, devoluciones y la opción `bill_for_rejected_quantity_in_purchase_invoice`; además completa `purchase_receipt`, `pr_detail`, `purchase_order` y `po_detail`. Purchase Receipt no está expuesto al Supplier en el portal estándar, por lo que la app debe ofrecer consultas mínimas propias.

Graphify ubica el flujo actual en `supplier_portal.py`, los dos DocTypes de auditoría, la página `registrar_factura`, sus assets y las pruebas. El código real confirma que esos componentes concentran identidad, reservas, idempotencia, archivos y creación del borrador.

## Goals / Non-Goals

**Goals:**

- Añadir un flujo claro e independiente para facturar cantidades recibidas.
- Reutilizar el mapeador y las validaciones nativas de ERPNext v15.
- Mantener aislamiento por Supplier e impedir manipulación de referencias y precios.
- Evitar reservas duplicadas y sobre-facturación concurrente.
- Reutilizar los servicios seguros ya probados.

**Non-Goals:**

- Dar acceso web directo al DocType Purchase Receipt.
- Soportar múltiples recepciones por factura o devoluciones.
- Cambiar lógica contable o de stock del core.

## Decisions

### Segunda página y menú

Se añade `/registrar-factura-recepcion` como opción `Facturar recepción`. Separar las fuentes evita controles ambiguos en un solo formulario y mantiene intacta la experiencia existente.

### Mapeador nativo de Purchase Receipt

La API usa `frappe.model.mapper.get_mapped_doc` con la tabla, filtros de cantidad y postprocesamiento del mapeador oficial `erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice`. El wrapper de ERPNext v15 no expone `ignore_permissions`; por ello el adaptador llama directamente al motor nativo con `ignore_permissions=True`, después de validar y bloquear la recepción. No cambia el usuario de sesión ni hardcodea un usuario privilegiado. Solo reemplaza las cantidades por valores previamente validados y agrega datos del comprobante, metadatos fiscales y observación de auditoría.

### Fuente discriminada en el registro auditado

`Supplier Invoice Submission` recibe `source_type` con opciones `Purchase Order` y `Purchase Receipt`, más un vínculo `purchase_receipt`. Exactamente uno de los dos vínculos debe coincidir con el tipo. El child recibe `purchase_receipt_item`; las columnas cuantitativas se mantienen como snapshots genéricos. Los registros históricos sin `source_type` se interpretan como Purchase Order.

### Disponibilidad basada en reglas nativas

La cantidad base se deriva con la misma regla usada por ERPNext: `qty` o `received_qty` según Buying Settings. Se restan cantidades facturadas enviadas por `pr_detail`, devoluciones aplicables y reservas activas del portal. Antes de insertar se bloquea la fila padre de Purchase Receipt y se recalcula el saldo.

### Seguridad y transacción

La sesión debe corresponder a un Website User con rol Supplier y una sola asociación Supplier. Supplier, Company, Currency, Item, Rate y referencias provienen del servidor. Registro, Purchase Invoice y archivos permanecen en una sola transacción sin commit manual.

### Servicios compartidos

Se conservan la clave idempotente por Supplier/número, detección contra Purchase Invoice, validación PDF/XML, adaptador fiscal y sincronización de estados. La interfaz de historial devuelve `source_type` y `source_name` sin revelar documentos de terceros.

## Affected Components

- `portales_web/hooks.py`.
- `portales_web/api/supplier_portal.py`.
- `Supplier Invoice Submission` y su controlador.
- `Supplier Invoice Submission Item`.
- `portales_web/www/registrar_factura_recepcion.py` y `.html`.
- `portales_web/public/js/supplier_receipt_invoice_portal.js`.
- Pruebas unitarias e integración del portal.
- Sin cambios en core, fixtures o reportes.

## Risks / Trade-offs

- [Diferencias de cantidad aceptada/rechazada] → Reutilizar configuración y mapeador nativos y cubrir ambos caminos con pruebas.
- [Devoluciones posteriores] → Excluir documentos de devolución y descontar retornos vinculados antes de reservar.
- [Carreras entre portal y usuarios internos] → Bloqueo de la recepción, recálculo bajo transacción y validación nativa al insertar.
- [Registros existentes] → Tratar `source_type` vacío como Purchase Order y hacer campos nuevos no destructivos.
- [Impuestos recalculados] → Mostrar `expected_total` y varianza; el documento queda Draft para revisión.
- [Cambios internos entre versiones] → Compatibilidad declarada solo con ERPNext/Frappe v15 y pruebas sobre el mapeador instalado.

## Migration Plan

1. Aplicar los cambios de código en la rama dedicada.
2. Ejecutar validaciones estáticas y unitarias sin modificar el sitio.
3. Con autorización explícita, ejecutar `bench --site v15.local migrate` para materializar campos nuevos.
4. Ejecutar pruebas de integración, incluida concurrencia, y verificar ambos flujos.
5. Regenerar Graphify y confirmar que sus artefactos siguen ignorados.

La reversión funcional consiste en retirar el menú y endpoints nuevos. Los campos aditivos pueden permanecer sin uso; no se eliminarán tablas ni datos. Las Purchase Invoices ya creadas se conservan como documentos contables y cualquier cancelación se realiza por el flujo estándar.
