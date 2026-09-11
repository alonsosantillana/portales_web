## Context

`_map_purchase_receipt_to_invoice` usa `get_mapped_doc`, que también copia campos personalizados compatibles por nombre. Luego `_make_purchase_invoice_from_receipt` llama a `_apply_purchase_invoice_fiscal_metadata`. Este último compara los valores actuales con los esperados y rechaza cualquier diferencia. La combinación es incorrecta para `tipo_comprobante`: en Purchase Receipt representa una guía, mientras que en Purchase Invoice debe representar la factura del proveedor.

Graphify confirmó la ruta `submit_invoice_from_receipt` → `_make_purchase_invoice_from_receipt` → `_map_purchase_receipt_to_invoice` / `_apply_purchase_invoice_fiscal_metadata`, y la revisión directa del código confirmó que el adaptador se comparte con el flujo de Purchase Order.

## Goals / Non-Goals

**Goals:**

- Corregir la transformación semántica entre recepción y factura.
- Conservar la procedencia canónica de valores fiscales en servidor.
- Mantener estricto el comportamiento del flujo por Purchase Order.
- Cubrir el caso real observado sin hardcodear el nombre de una guía específica.

**Non-Goals:**

- Modificar la recepción o sus catálogos.
- Cambiar el modelo fiscal general de Ovenube.
- Procesar o validar semánticamente el XML adjunto.

## Decisions

### Sobrescritura explícita y privada

Se añadirá a `_apply_purchase_invoice_fiscal_metadata` un parámetro interno `overwrite_existing=False`. `_make_purchase_invoice_from_receipt` será el único llamador que lo active. El endpoint no expondrá el parámetro y seguirá ignorando cualquier metadata fiscal del navegador.

### Recalcular todos los campos fiscales canónicos

Cuando la sobrescritura esté activada, el adaptador asignará `tipo_comprobante`, `codigo_comprobante`, `tipo_documento_identidad` y `codigo_tipo_documento` desde los catálogos y el Supplier. Esto evita conservar combinaciones incoherentes heredadas del documento fuente.

### Mantener validación estricta por defecto

Sin el indicador explícito, un valor actual diferente del catálogo seguirá provocando el mismo error. Así no se ocultan inconsistencias en el flujo existente desde Purchase Order ni en futuros llamadores.

## Affected Components

- API interna: `portales_web/api/supplier_portal.py`.
- Pruebas: `portales_web/tests/test_supplier_portal.py` y `portales_web/tests/test_supplier_portal_integration.py`.
- DocTypes, hooks, reportes, fixtures y core: sin cambios.

## Risks / Trade-offs

- [Ocultar datos fiscales incorrectos] → La sobrescritura no es global; solo aplica al documento creado en memoria desde una recepción autorizada.
- [Catálogo o Supplier inválido] → Se conservan todas las verificaciones existentes y la transacción falla antes de insertar la factura.
- [Regresión en Purchase Order] → El valor predeterminado permanece estricto y se cubre con una prueba específica.
- [Dependencia de un nombre concreto de guía] → La prueba obtiene cualquier comprobante de catálogo distinto del código `01`.

## Migration and Rollback

No se requiere `bench migrate`. La reversión restaura la llamada y la firma anteriores; no deja cambios de esquema ni modifica recepciones existentes.
