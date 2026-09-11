## Context

`Supplier Invoice Submission.on_trash` bloquea actualmente cualquier registro con `purchase_invoice`. El hook `sync_purchase_invoice_status` atiende `on_submit`, `on_cancel` y `on_trash` de Purchase Invoice, pero en `on_trash` solo asigna Rechazada. Como el Link permanece, la solicitud no puede eliminarse aun después de borrar la factura.

Graphify ubica el controlador, el hook de Purchase Invoice y las pruebas como la comunidad afectada. El grafo local contenía referencias de una rama funcional posterior, por lo que sus hallazgos se consideran orientativos y se confirmaron contra los archivos reales de `version-15` antes de diseñar este cambio.

## Goals / Non-Goals

**Goals:**

- Establecer un orden de eliminación explícito y seguro.
- Evitar vínculos colgantes después de eliminar una Purchase Invoice.
- Conservar el comportamiento existente de Submit y Cancel.
- Mantener cambios mínimos y compatibles con Frappe/ERPNext v15.

**Non-Goals:**

- Automatizar el borrado de documentos relacionados.
- Cambiar permisos, DocTypes o el flujo del proveedor.
- Alterar asientos contables, impuestos o validaciones nativas.

## Decisions

### Exigir la eliminación de la Factura de Compra primero

La solicitud seguirá bloqueada mientras la Factura de Compra exista, incluso si está cancelada. Así se evita dejar una factura apuntando a un registro eliminado o depender de una cascada implícita. El mensaje indicará cancelar la factura enviada y eliminarla antes de reintentar.

### Desvincular desde el hook `on_trash` de Purchase Invoice

El hook existente es el punto en que se conoce de forma inequívoca qué factura se está eliminando. En ese evento se guarda la solicitud con estado Rechazada y `purchase_invoice` vacío. Submit y Cancel conservarán el vínculo y solo actualizarán el estado.

### Tolerar vínculos históricos inválidos

Si el campo conserva un nombre pero la Purchase Invoice ya no existe, `on_trash` de la solicitud no bloqueará su eliminación. Esto permite limpiar datos heredados sin SQL ni cambios masivos.

## Affected Components

- DocType: `Supplier Invoice Submission` (controlador; sin cambio de esquema).
- Hook: eventos existentes de `Purchase Invoice` en `portales_web/hooks.py` (sin cambio de configuración).
- Pruebas: `portales_web/tests/test_supplier_portal.py` y `portales_web/tests/test_supplier_portal_integration.py`.
- APIs, reportes, fixtures y core: sin cambios.

## Risks / Trade-offs

- [Pérdida del vínculo visible al borrar la factura] → Es consecuencia intencional de eliminar el documento; se conserva la solicitud Rechazada hasta que un usuario decida eliminarla por separado.
- [Borrado accidental en cascada] → No se implementa ninguna cascada; son dos acciones manuales y controladas por permisos estándar.
- [Regresión de estados] → Pruebas unitarias separan `on_submit`, `on_cancel` y `on_trash`, y una prueba de integración cubre el ciclo real.
- [Datos históricos con vínculo inválido] → Se permite eliminar la solicitud únicamente cuando el destino del vínculo no existe.

## Migration and Rollback

No se requiere `bench migrate`. Para revertir, se restaura el controlador anterior; no se crean campos ni patches. Las solicitudes ya desvinculadas durante el uso del cambio permanecen válidas como registros Rechazados y pueden volver a vincularse manualmente solo tras una revisión funcional.
