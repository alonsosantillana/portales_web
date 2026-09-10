## Purpose

Garantizar que cada usuario de portal opere únicamente dentro del Supplier autorizado por ERPNext y pueda acceder a una interfaz de registro autenticada.

## ADDED Requirements

### Requirement: Identidad basada en Portal User

El sistema SHALL resolver el Supplier desde la tabla `Portal User` del Supplier y SHALL exigir que el usuario autenticado tenga el rol Supplier.

#### Scenario: Usuario con un Supplier autorizado

- **WHEN** un Website User con rol Supplier está relacionado con exactamente un Supplier mediante `Supplier.portal_users`
- **THEN** el sistema usa ese Supplier como identidad efectiva para todas las consultas y escrituras

#### Scenario: Identidad ambigua o inexistente

- **WHEN** el usuario no tiene Supplier autorizado o está asociado con más de uno
- **THEN** el sistema rechaza la operación sin revelar documentos de ningún Supplier

### Requirement: Aislamiento de órdenes y registros

El sistema SHALL devolver únicamente Órdenes de Compra y registros cuyo Supplier coincida con la identidad efectiva del usuario.

#### Scenario: Consulta autorizada

- **WHEN** el proveedor consulta sus órdenes elegibles o sus registros
- **THEN** recibe exclusivamente documentos de su Supplier

#### Scenario: Identificador de otro proveedor

- **WHEN** el usuario envía manualmente el nombre de una OC o registro de otro Supplier
- **THEN** el servidor responde con un error de permiso y no revela datos del documento

### Requirement: Página autenticada

El sistema SHALL publicar la ruta `registrar-factura` solamente para usuarios autenticados con contexto Supplier válido.

#### Scenario: Acceso Guest

- **WHEN** un usuario Guest intenta abrir la página o invocar sus APIs
- **THEN** el sistema exige autenticación y no devuelve información de compras
