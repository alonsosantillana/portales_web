## ADDED Requirements

### Requirement: Recepción elegible y aislada

El sistema SHALL mostrar únicamente Purchase Receipts del Supplier autenticado que estén enviadas, no sean devoluciones y tengan al menos una cantidad pendiente de facturar.

#### Scenario: Recepción propia disponible

- **WHEN** un Supplier autenticado consulta sus recepciones
- **THEN** recibe solo documentos propios con saldo facturable

#### Scenario: Recepción ajena o inválida

- **WHEN** el cliente envía el identificador de otro Supplier, una devolución o un documento no enviado
- **THEN** el servidor rechaza la operación sin revelar sus datos

### Requirement: Cantidad facturable por recepción

El sistema SHALL calcular el saldo con las reglas nativas de ERPNext, descontando facturas enviadas, devoluciones aplicables y reservas activas por Purchase Receipt Item.

#### Scenario: Facturación parcial

- **WHEN** el proveedor solicita una cantidad positiva menor o igual al saldo
- **THEN** el sistema acepta esa cantidad y conserva el remanente para otra factura

#### Scenario: Sobre-facturación concurrente

- **WHEN** dos solicitudes intentan reservar más que el saldo de una recepción
- **THEN** el bloqueo y recálculo transaccional permiten solo las cantidades disponibles

### Requirement: Mapeo nativo a Purchase Invoice

El sistema SHALL crear una Purchase Invoice Draft usando el mapeador de Purchase Receipt de ERPNext v15.

#### Scenario: Creación exitosa

- **WHEN** la recepción, ítems, comprobante y adjuntos pasan las validaciones
- **THEN** se crea una Purchase Invoice Draft con `purchase_receipt` y `pr_detail` correctos
- **AND** se conservan `purchase_order` y `po_detail` cuando provienen de una orden

#### Scenario: Validación nativa fallida

- **WHEN** ERPNext rechaza la factura por una regla contable o de compras
- **THEN** la transacción no conserva el registro, la factura ni sus adjuntos

### Requirement: Archivos, identidad e idempotencia compartidos

El sistema SHALL aplicar al flujo por recepción los mismos controles de Supplier efectivo, número duplicado, PDF/XML privado y metadatos fiscales del flujo existente.

#### Scenario: Número ya registrado

- **WHEN** el Supplier reenvía un número normalizado existente
- **THEN** el sistema devuelve el registro idempotente o rechaza el duplicado contable sin crear otra factura
