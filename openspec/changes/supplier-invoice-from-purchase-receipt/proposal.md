## Why

El proveedor actualmente puede registrar facturas únicamente contra una Orden de Compra. Cuando la empresa factura según cantidades efectivamente recibidas, el proveedor necesita seleccionar una Recepción de Compra propia y crear desde ella una Purchase Invoice Draft sin obtener permisos internos ni poder alterar proveedor, compañía, moneda, precios o referencias contables.

## What Changes

- Añadir una segunda opción de portal `Facturar recepción` en la ruta `/registrar-factura-recepcion`.
- Exponer endpoints filtrados para consultar Recepciones de Compra elegibles y sus cantidades pendientes.
- Crear la Purchase Invoice Draft mediante el mapeador nativo de Purchase Receipt de ERPNext v15.
- Extender el registro auditado existente para identificar si el origen es Purchase Order o Purchase Receipt.
- Reservar cantidades por Purchase Receipt Item y bloquear la recepción durante la creación transaccional.
- Reutilizar validación de identidad, duplicados, adjuntos privados, metadatos fiscales y sincronización de estados.
- Mostrar el tipo y documento de origen en el historial del proveedor.

## Capabilities

### New Capabilities

- `supplier-invoice-from-purchase-receipt`: Registro seguro de una factura de proveedor desde una Recepción de Compra enviada, con cantidades parciales y Purchase Invoice Draft.

### Modified Capabilities

- `supplier-invoice-submission`: El registro auditado admite Purchase Order o Purchase Receipt como orígenes mutuamente excluyentes.
- `supplier-portal-access`: El portal ofrece una segunda ruta autenticada y aislada para Recepciones de Compra.

## Scope

Una factura se genera desde una sola Recepción de Compra no devuelta, enviada y perteneciente al Supplier autenticado. Se admiten cantidades parciales pendientes, PDF/XML obligatorios y creación en borrador para revisión interna.

## Exclusions

- Agrupar varias Recepciones de Compra en una factura.
- Facturar devoluciones o crear notas de crédito.
- Submit, contabilización o pago automático.
- Lectura semántica del XML o validación externa SUNAT.
- Cambios en `apps/frappe` o `apps/erpnext`.

## Expected Impact

- Base de datos: campos aditivos en los dos DocTypes de auditoría existentes y relajación controlada de la obligatoriedad de Purchase Order.
- Compras: nueva Purchase Invoice Draft referenciada por `purchase_receipt` y `pr_detail` mediante el mapeador nativo.
- Seguridad: acceso exclusivo por APIs que resuelven el Supplier desde la sesión.
- Portal: una nueva opción independiente; el flujo por Orden de Compra se conserva.

## Acceptance Criteria

- El Supplier solo visualiza Recepciones de Compra propias, enviadas, no devueltas y con saldo facturable.
- El servidor rechaza recepciones e ítems ajenos, cancelados, devueltos, repetidos o sin saldo.
- Las cantidades pendientes respetan Purchase Invoices enviadas, devoluciones y la configuración nativa sobre cantidad rechazada.
- Solicitudes activas reservan cantidades y evitan sobre-facturación concurrente.
- La Purchase Invoice se construye con el mapeador nativo de Purchase Receipt y permanece en Draft.
- Los ítems creados contienen `purchase_receipt` y `pr_detail`; las referencias a Purchase Order se conservan cuando existen.
- PDF/XML son privados y se conservan los controles de duplicado y metadatos fiscales existentes.
- El historial identifica correctamente el tipo y documento de origen.
- El flujo existente desde Purchase Order sigue funcionando y sus pruebas no presentan regresiones.

## Impact

- App: `portales_web`.
- DocTypes: `Supplier Invoice Submission`, `Supplier Invoice Submission Item`.
- Hooks: menú de portal y regla de ruta.
- API: `portales_web.api.supplier_portal`.
- Web: nueva página y JavaScript del flujo por recepción; historial compartido actualizado.
- Fixtures, reportes y core: ninguno.
