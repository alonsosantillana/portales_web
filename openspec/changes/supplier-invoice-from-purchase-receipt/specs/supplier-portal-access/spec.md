## MODIFIED Requirements

### Requirement: Opciones independientes de registro

El portal SHALL ofrecer al rol Supplier una opción para facturar Órdenes de Compra y otra para facturar Recepciones de Compra.

#### Scenario: Navegación del Supplier

- **WHEN** un Website User con rol Supplier abre el menú del portal
- **THEN** puede seleccionar `Registrar factura` o `Facturar recepción`

#### Scenario: Acceso Guest

- **WHEN** un usuario Guest intenta abrir cualquiera de las rutas
- **THEN** es redirigido al login con retorno a la ruta solicitada

### Requirement: Historial aislado con origen

El historial SHALL mostrar solo registros del Supplier efectivo e identificar el tipo y nombre de su documento de origen.

#### Scenario: Historial mixto

- **WHEN** el Supplier tiene facturas desde órdenes y recepciones
- **THEN** visualiza ambas sin acceder a registros de otros Suppliers
