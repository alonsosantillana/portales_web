## Why

Al cancelar una Factura de Compra creada desde el portal, la solicitud relacionada cambia a Rechazada pero conserva el vínculo. Si un usuario interno intenta eliminar la solicitud, el controlador bloquea la operación incluso cuando la factura ya fue cancelada. Esto impide completar una limpieza explícita y ordenada de ambos documentos.

## What Changes

- Mantener protegida la solicitud mientras exista cualquier Factura de Compra vinculada.
- Indicar al usuario el orden seguro: cancelar la factura si corresponde y eliminar primero la Factura de Compra.
- Cuando ERPNext elimine la Factura de Compra, marcar la solicitud como Rechazada y retirar su vínculo antes de finalizar la eliminación.
- Permitir después la eliminación manual de la solicitud desvinculada.
- Cubrir con pruebas el bloqueo, los vínculos históricos inválidos y la sincronización de eventos.

## Scope

El cambio se limita al ciclo interno de eliminación de `Purchase Invoice` y `Supplier Invoice Submission`, su hook existente y sus pruebas. No cambia el portal del proveedor ni crea campos.

## Exclusions

- Eliminación en cascada o automática de la solicitud.
- Permisos de eliminación para usuarios Supplier.
- Eliminación o modificación de registros existentes como parte del despliegue.
- Cambios en `apps/frappe`, `apps/erpnext`, contabilidad, impuestos, totales o archivos adjuntos.

## Expected Impact

- Base de datos: sin cambios de esquema ni migración.
- Contabilidad: la Factura de Compra debe estar cancelada antes de poder eliminarse conforme a ERPNext.
- Auditoría: la solicitud queda Rechazada y desvinculada cuando se elimina la factura; su eliminación posterior continúa siendo una acción manual y separada.
- Seguridad: se conservan los permisos estándar de ambos DocTypes.

## Acceptance Criteria

- Una solicitud vinculada a una Factura de Compra existente no puede eliminarse y recibe una instrucción accionable.
- Eliminar una Factura de Compra cancelada desvincula su solicitud y conserva el estado Rechazada.
- La eliminación de la factura no elimina automáticamente la solicitud.
- Una solicitud desvinculada puede eliminarse según sus permisos estándar.
- Un vínculo histórico cuyo documento ya no existe no bloquea la eliminación de la solicitud.
- Submit y Cancel siguen sincronizando Procesada y Rechazada sin retirar el vínculo.
- Las pruebas y OpenSpec validan correctamente.
