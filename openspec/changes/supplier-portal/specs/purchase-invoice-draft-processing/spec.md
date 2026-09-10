## Purpose

Crear Purchase Invoices Draft coherentes con ERPNext mediante validaciones transaccionales que soporten facturación parcial sin sobrepasar cantidades disponibles.

## ADDED Requirements

### Requirement: Orden elegible

El sistema SHALL aceptar únicamente una Purchase Order enviada, no cerrada ni cancelada y perteneciente al Supplier efectivo.

#### Scenario: Orden válida

- **WHEN** el proveedor selecciona una OC enviada y abierta de su Supplier
- **THEN** el sistema permite consultar sus ítems con saldo disponible

#### Scenario: Orden inválida

- **WHEN** la OC no está enviada, está cerrada/cancelada o pertenece a otro Supplier
- **THEN** el sistema bloquea la consulta y el registro

### Requirement: Cantidades disponibles

El sistema SHALL calcular el saldo desde la cantidad ordenada menos la cantidad de Purchase Invoice enviada y menos las cantidades reservadas por solicitudes activas del portal.

#### Scenario: Facturación parcial válida

- **WHEN** la cantidad solicitada es positiva y no supera el saldo recalculado
- **THEN** el sistema reserva esa cantidad y permite crear el borrador

#### Scenario: Sobre-facturación o concurrencia

- **WHEN** una cantidad supera el saldo o otra transacción lo reservó primero
- **THEN** el sistema rechaza la operación sin crear documentos parciales

### Requirement: Mapeo nativo a Purchase Invoice

El sistema SHALL usar el mapeador estándar de Purchase Order para conservar cuentas, impuestos, conversiones y referencias, y SHALL crear la Purchase Invoice con `docstatus = 0`.

#### Scenario: Creación exitosa

- **WHEN** todos los datos, cantidades y archivos son válidos
- **THEN** se crea una sola Purchase Invoice Draft relacionada con la OC y la solicitud

#### Scenario: Validación contable nativa fallida

- **WHEN** ERPNext exige una condición no satisfecha, como Purchase Receipt obligatorio
- **THEN** toda la operación se revierte y el proveedor recibe un error controlado

### Requirement: Metadata fiscal condicional

Cuando Purchase Invoice contiene los campos fiscales de Ovenube, el sistema SHALL derivar el comprobante Factura desde el registro de catálogo con código SUNAT `01` y SHALL derivar la identidad desde el Supplier, validando nombre y código contra el catálogo de documentos de identidad. El sistema SHALL ignorar cualquier intento del navegador de controlar esos campos.

#### Scenario: Esquema fiscal completo

- **WHEN** el sitio tiene los campos y catálogos fiscales configurados y el Supplier posee una identidad coherente
- **THEN** la Purchase Invoice Draft recibe los cuatro valores fiscales validados antes de su inserción

#### Scenario: Catálogo o identidad inconsistente

- **WHEN** falta un registro requerido o el nombre y código del Supplier no coinciden con el catálogo
- **THEN** toda la operación se revierte con un error de configuración sin omitir campos obligatorios

#### Scenario: ERPNext sin extensión fiscal

- **WHEN** los campos fiscales de Ovenube no existen en Purchase Invoice
- **THEN** el adaptador no altera el documento mapeado

### Requirement: Sincronización del resultado

El sistema SHALL marcar la solicitud como Procesada cuando la Purchase Invoice sea enviada y como Rechazada cuando sea cancelada.

#### Scenario: Submit interno

- **WHEN** un usuario interno envía la Purchase Invoice
- **THEN** el registro relacionado cambia a Procesada

#### Scenario: Cancelación interna

- **WHEN** un usuario interno cancela la Purchase Invoice
- **THEN** el registro relacionado cambia a Rechazada
