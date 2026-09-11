## Why

Cuando un usuario interno elimina una Purchase Invoice, el hook conserva la `Supplier Invoice Submission` como Rechazada y retira el vínculo contable. Si el proveedor reintenta el mismo número de factura desde la misma Purchase Receipt, la clave idempotente encuentra el registro histórico y devuelve `duplicate = true` con `purchase_invoice = null`. Esto impide un reintento válido y produce un mensaje confuso.

## What Changes

- Reutilizar la misma solicitud cuando esté Rechazada, no tenga Purchase Invoice y pertenezca a la misma Purchase Receipt.
- Bloquear y releer la solicitud antes de reutilizarla para evitar dos reintentos concurrentes.
- Revalidar proveedor, recepción, cantidades, número, fecha, total, archivos y metadata fiscal con las reglas actuales.
- Actualizar la solicitud existente y sus ítems dentro de la misma transacción, crear una nueva Purchase Invoice Draft y vincularla.
- Mantener bloqueados los duplicados activos, vinculados o procedentes de otro documento.
- Evitar que la interfaz muestre `Purchase Invoice null` cuando exista un duplicado sin vínculo que no pueda reintentarse.

## Scope

El cambio cubre exclusivamente reintentos desde Purchase Receipt. Conserva el mismo identificador de solicitud para mantener trazabilidad.

## Exclusions

- Reintentos automáticos desde Purchase Order.
- Eliminar solicitudes, facturas, adjuntos o datos históricos.
- Reutilizar solicitudes Procesadas, En revisión, Observadas o con Purchase Invoice vinculada.
- Cambios en contabilidad, impuestos, catálogos, series, correlativos o integración electrónica.
- Cambios en `apps/frappe` o `apps/erpnext`.

## Expected Impact

- Auditoría: el mismo registro pasa de Rechazada a En revisión al completar el reintento, conservando Track Changes.
- Idempotencia: la clave única se conserva y sigue impidiendo documentos paralelos.
- Compras: cantidades y disponibilidad se recalculan antes del nuevo borrador.
- Base de datos: sin cambios de esquema ni migración.

## Acceptance Criteria

- Una solicitud Rechazada, sin Purchase Invoice y del mismo recibo puede reintentarse.
- El reintento conserva el nombre de la solicitud y crea una nueva Purchase Invoice Draft.
- Datos editables, ítems y adjuntos se reemplazan por los enviados en el nuevo intento después de validarlos.
- Una solicitud vinculada, activa, procesada o de otro origen continúa respondiendo como duplicado.
- Dos reintentos concurrentes no crean dos Purchase Invoices.
- Una falla durante el reintento revierte la solicitud a su estado previo.
- La interfaz no imprime la palabra `null` para duplicados sin Purchase Invoice.
- OpenSpec y las pruebas validan correctamente.
