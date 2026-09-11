## Context

`submit_invoice_from_receipt` consulta `_get_existing_submission` antes de validar y bloquear la Purchase Receipt. Cualquier coincidencia se devuelve mediante `_existing_submission_response`, sin distinguir estado ni vínculo. La clave `supplier_invoice_key` es única por Supplier y número normalizado, por lo que insertar otra solicitud no es correcto; el registro rechazado debe reutilizarse de manera controlada.

Graphify confirmó la ruta entre `submit_invoice_from_receipt`, `_get_existing_submission`, `_existing_submission_response`, el controlador de la solicitud y las pruebas. La inspección directa del registro `SIS-2026-09485` confirmó estado Rechazada, origen `PREC-03486` y `purchase_invoice = null`.

## Goals / Non-Goals

**Goals:**

- Permitir corregir un reintento legítimo sin perder auditoría.
- Mantener exclusión mutua e idempotencia ante concurrencia.
- Ejecutar nuevamente todas las validaciones de negocio y seguridad.
- Mejorar el mensaje para duplicados sin factura vinculada.

**Non-Goals:**

- Crear un segundo registro con la misma clave.
- Reintentar contra una recepción distinta.
- Recuperar o reutilizar archivos del intento anterior.
- Cambiar permisos del proveedor sobre DocTypes internos.

## Decisions

### Reutilizar solo Rechazada + sin vínculo + mismo recibo

La elegibilidad exige `status = Rechazada`, `purchase_invoice` vacío, `source_type = Purchase Receipt` y `purchase_receipt` igual al solicitado. Cualquier otra combinación conserva la respuesta de duplicado.

### Bloquear y releer antes de decidir

Una consulta `FOR UPDATE` bloqueará la fila de `Supplier Invoice Submission`. Después se cargará nuevamente el documento y se repetirá la validación de elegibilidad. Si otro proceso ya lo reutilizó, el segundo devuelve la respuesta idempotente actualizada.

### Preparar nuevamente el registro dentro de la transacción

Después de validar y bloquear la Purchase Receipt, se prepararán en memoria fecha, total, observación, usuario, moneda e ítems, y se limpiarán el vínculo contable y valores calculados. El estado temporal será Registrada. El documento solo se guardará después de completar el mapeo y los nuevos adjuntos privados, ya en estado En revisión; así no depende de referencias antiguas para satisfacer campos obligatorios.

Si cualquier paso falla, el rollback de la petición restaura la solicitud Rechazada y sus datos anteriores.

### Mensaje seguro sin `null`

La interfaz construirá el texto según exista o no `purchase_invoice`. Un duplicado sin vínculo mostrará el registro y su estado, sin afirmar que existe una Purchase Invoice en borrador.

## Affected Components

- API: `portales_web/api/supplier_portal.py`.
- JavaScript: `portales_web/public/js/supplier_receipt_invoice_portal.js`.
- Pruebas: `portales_web/tests/test_supplier_portal.py` y `portales_web/tests/test_supplier_portal_integration.py`.
- DocTypes, hooks, fixtures, reportes y core: sin cambios.

## Risks / Trade-offs

- [Dos reintentos simultáneos] → Bloqueo de la solicitud, relectura y clave única existente.
- [Reserva de cantidades obsoleta] → Rechazada no reserva; la disponibilidad se recalcula después de bloquear la recepción.
- [Pérdida de auditoría] → Se conserva el mismo documento y Track Changes; no se elimina el registro.
- [Archivos anteriores] → No se reutilizan; los nuevos adjuntos privados sustituyen sus referencias después de validación.
- [Falla intermedia] → No hay commit manual; Frappe revierte todos los cambios de la petición.

## Migration and Rollback

No se requiere `bench migrate`. La reversión restaura el retorno idempotente inmediato y el mensaje previo; las solicitudes ya reutilizadas continúan siendo registros válidos vinculados a su nueva Purchase Invoice.
