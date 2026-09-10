## Why

Los proveedores necesitan registrar sus comprobantes contra Órdenes de Compra sin recibir permisos de creación sobre Purchase Invoice ni acceder a documentos de otros proveedores. El proceso debe conservar las validaciones contables de ERPNext v15, soportar facturación parcial y entregar a Contabilidad una Purchase Invoice en borrador con evidencia privada.

## What Changes

- Reutilizar las vistas estándar del portal ERPNext para consultar Órdenes de Compra y Facturas de Compra autorizadas.
- Crear una página autenticada `registrar-factura` dentro de `portales_web` para seleccionar una OC, confirmar cantidades y adjuntar PDF/XML.
- Crear los DocTypes estándar `Supplier Invoice Submission` y `Supplier Invoice Submission Item` para auditoría, estados, reservas e idempotencia.
- Resolver la identidad del proveedor exclusivamente desde `Supplier.portal_users` y el rol Supplier.
- Crear endpoints de lectura filtrados y un endpoint POST transaccional que ignore datos sensibles enviados por el navegador.
- Generar Purchase Invoice Draft mediante el mapeador nativo de Purchase Order y conservar las validaciones de ERPNext.
- Completar condicionalmente los metadatos fiscales obligatorios de Ovenube desde el Supplier y sus catálogos, sin aceptar esos valores desde el navegador.
- Guardar PDF y XML como archivos privados y reasociarlos a la Purchase Invoice creada.
- Sincronizar el estado del registro cuando la Purchase Invoice sea enviada o cancelada.
- Añadir pruebas de aislamiento, manipulación, duplicados, cantidades y permisos.

## Capabilities

### New Capabilities

- `supplier-portal-access`: Acceso autenticado y aislado a la página de registro, las órdenes elegibles y los registros pertenecientes al Supplier del usuario.
- `supplier-invoice-submission`: Registro idempotente de datos, cantidades y adjuntos privados de una factura de proveedor contra una sola OC.
- `purchase-invoice-draft-processing`: Validación transaccional, reserva de cantidades y creación de Purchase Invoice Draft mediante reglas nativas de ERPNext.

### Modified Capabilities

Ninguna.

## Scope

El MVP cubre una factura contra una Orden de Compra enviada, facturación total o parcial, archivos PDF/XML obligatorios, consulta de estado y creación automática de una Purchase Invoice Draft para revisión interna.

## Exclusions

- Lectura semántica del XML, consulta SUNAT, CDR, detracciones y retenciones personalizadas.
- 3-way matching obligatorio con Purchase Receipt; se respetará cualquier validación nativa configurada en ERPNext.
- Submit automático de Purchase Invoice, pagos o contabilización automática.
- Facturas que agrupen varias Órdenes de Compra.
- Notificaciones por correo y flujo de aprobación configurable.
- Cambios en `apps/frappe` o `apps/erpnext`.

## Expected Impact

- Base de datos: dos DocTypes nuevos y sus tablas al instalar/migrar la app.
- Seguridad: rol Supplier sin permisos de creación/escritura sobre Purchase Invoice; operaciones sensibles concentradas en servidor.
- Contabilidad: nuevas Purchase Invoices en `docstatus = 0`; ninguna contabilización automática.
- Archivos: PDF/XML privados asociados al documento contable.
- Portal: nueva ruta y menú para Supplier; las listas estándar existentes continúan sin modificaciones.

## Acceptance Criteria

- Un usuario Supplier asociado a un único Supplier puede registrar una factura de una OC propia.
- Un usuario Guest, sin Supplier, con varios Suppliers o de otro Supplier es rechazado.
- Supplier, Company, Currency, Item, Rate y saldo se derivan en servidor.
- No se aceptan ítems ajenos a la OC, cantidades no positivas ni cantidades mayores al saldo disponible.
- Solicitudes activas reservan cantidad y evitan crear borradores concurrentes por encima del saldo.
- El mismo Supplier no puede registrar dos veces el mismo número normalizado de factura.
- PDF/XML quedan privados y vinculados a la Purchase Invoice Draft.
- La Purchase Invoice se construye con el mapeador nativo y permanece en Draft.
- Cuando el esquema fiscal de Ovenube está presente, la factura usa el comprobante de catálogo SUNAT `01` y la identidad validada del Supplier.
- El Supplier no obtiene permisos directos para crear, editar o enviar Purchase Invoice.
- Las pruebas y OpenSpec validan correctamente antes de solicitar instalación o migración.

## Impact

- App afectada: `portales_web`.
- Módulo: Portales Web.
- DocTypes: `Supplier Invoice Submission` y `Supplier Invoice Submission Item`.
- Hooks: menú de portal y eventos de Purchase Invoice.
- APIs: nuevo módulo `portales_web.api.supplier_portal`.
- Web: nueva página `registrar-factura` y JavaScript asociado.
- Fixtures y reportes: ninguno.
