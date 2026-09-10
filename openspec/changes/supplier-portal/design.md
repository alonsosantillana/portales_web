## Context

ERPNext v15 ya publica listas de Purchase Order y Purchase Invoice para el rol Supplier y aplica filtros web mediante `Supplier.portal_users`. También dispone de un mapeador de Purchase Order a Purchase Invoice que calcula cantidades facturadas desde documentos enviados. La app `portales_web` todavía no contiene lógica funcional y su grafo inicial tiene 8 nodos y 0 relaciones.

La propuesta original usa Contact Email como autoridad, consulta un campo `billed_qty` inexistente en Purchase Order Item, construye la factura manualmente y confía en un Web Form genérico. Estas decisiones se reemplazan para preservar seguridad, reglas contables y compatibilidad.

## Goals / Non-Goals

**Goals:**

- Reutilizar el portal estándar para lectura y añadir únicamente el flujo de registro faltante.
- Mantener todas las escrituras sensibles en una API POST de servidor.
- Crear un registro auditable y una Purchase Invoice Draft atómicamente.
- Evitar duplicados y sobre-facturación, incluso ante solicitudes concurrentes.
- Mantener archivos privados y no modificar core.

**Non-Goals:**

- Procesar semánticamente XML o validar SUNAT.
- Automatizar Submit, contabilización o pagos.
- Implementar 3-way matching más allá de respetar validaciones nativas.
- Soportar múltiples Suppliers por usuario o múltiples OCs por factura en el MVP.

## Decisions

### Reutilizar las listas estándar de ERPNext

Se conservan `/purchase-orders` y `/purchase-invoices`, cuyos permisos ya se basan en Portal User. La alternativa de duplicar las listas añade superficie de seguridad y mantenimiento sin aportar comportamiento nuevo.

### Usar una página web personalizada en lugar de Web Form

La página `registrar-factura` consumirá endpoints con respuestas mínimas y filtradas. Esto evita las limitaciones de opciones Link y el flujo genérico de inserción con `ignore_permissions` de Web Form. La API seguirá validando todo aunque el cliente sea manipulado.

### Un Supplier efectivo por sesión

El servidor consulta `get_parents_for_user("Supplier")` y exige exactamente un resultado. Esta restricción elimina selección ambigua en el MVP. Soportar múltiples Suppliers requeriría una selección explícita autorizada y pruebas adicionales.

### Registro no submittable con estado controlado

`Supplier Invoice Submission` conservará Track Changes y un estado que solo cambia desde servidor o usuarios internos. El proveedor no obtiene permisos directos sobre el DocType y opera mediante APIs filtradas. Se descarta hacer el registro submittable porque la corrección Observada requeriría enmiendas y ampliaría el MVP.

### Clave de factura e idempotencia

Una clave SHA-256 única derivada de Supplier y número normalizado evita carreras de duplicado. Las solicitudes rechazadas se corrigen en el mismo registro en una fase futura; el MVP no permite crear otra solicitud con la misma identidad.

### Reserva transaccional por ítem

El endpoint bloquea la fila de Purchase Order, recalcula cantidades enviadas y suma las solicitudes activas antes de insertar. La reserva queda representada en los ítems de la solicitud mientras su estado sea Registrada, En revisión u Observada.

### Mapeo nativo y transacción única

Se usa `get_mapped_purchase_invoice` con los ítems seleccionados, luego se reemplazan únicamente sus cantidades por valores ya validados. No se ejecuta `frappe.db.commit()` manual: la solicitud, factura y adjuntos pertenecen a la transacción de la petición.

### Archivos privados y canónicos

El endpoint valida nombre, tamaño y firma mínima, guarda los archivos con `is_private=1` y finalmente los reasocia a Purchase Invoice. Se evita copiar documentos File y producir referencias ambiguas.

### Enriquecimiento fiscal condicional de Purchase Invoice

Después del mapeo nativo y antes de insertar la Purchase Invoice, el servidor inspecciona su metadata. Si existen los cuatro campos fiscales de Ovenube, obtiene `tipo_comprobante` desde `Tipos de Comprobante` por el código SUNAT estable `01` y obtiene la identidad desde `Supplier.nombre_tipo_documento`/`Supplier.codigo_tipo_documento`, validándola contra `Tipos de Documento de Identidad`. Los valores preexistentes incompatibles se rechazan; el navegador no puede enviarlos. Si el esquema no existe, el adaptador no modifica la factura y la app conserva compatibilidad con ERPNext v15 sin Ovenube.

## Affected Components

- DocTypes: `Supplier Invoice Submission`, `Supplier Invoice Submission Item`.
- Hooks: `portal_menu_items`; eventos `on_submit`, `on_cancel` y `on_trash` de Purchase Invoice.
- APIs: `portales_web.api.supplier_portal`.
- Web: `portales_web/www/registrar-factura.*` y asset JavaScript.
- Reportes y fixtures: ninguno.
- Core: solo lectura/importación de APIs públicas/internas existentes; ningún archivo modificado.

## Risks / Trade-offs

- [Cambio interno en el mapeador entre versiones] → Fijar compatibilidad v15 y cubrir el adaptador con pruebas.
- [Dos solicitudes simultáneas] → Bloqueo `FOR UPDATE`, reserva activa y clave única.
- [Purchase Receipt obligatorio] → Respetar la validación nativa, revertir y mostrar un mensaje; diseñar 3-way matching en otro cambio.
- [Archivos maliciosos] → Privacidad, límite global, extensiones/firma y recomendación de antivirus antes de producción.
- [Número de factura previamente creado fuera del portal] → Validar también Purchase Invoice activa además de la clave del registro.
- [Correo o destinatarios no configurados] → No enviar notificaciones en el MVP ni hardcodear usuarios.
- [Catálogos fiscales ausentes o inconsistentes] → Detener la transacción con un error de configuración; nunca omitir campos obligatorios ni inferir etiquetas no catalogadas.

## Migration Plan

1. Instalar la app en un sitio de pruebas con autorización explícita.
2. Ejecutar migración para crear ambos DocTypes.
3. Asociar cada Website User en `Supplier.portal_users` y verificar rol Supplier.
4. Probar con dos Suppliers y documentos separados.
5. Validar archivos privados, concurrencia y flujo contable antes de producción.

La reversión previa a uso consiste en desinstalar la app con autorización. Si existen registros o Purchase Invoices, conservar los documentos contables y retirar primero menú/endpoints; cualquier eliminación de tablas o datos requiere un plan separado.
