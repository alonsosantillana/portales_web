## MODIFIED Requirements

### Requirement: Mapeo nativo a Purchase Invoice

El sistema SHALL crear una Purchase Invoice Draft usando el mapeador de Purchase Receipt de ERPNext v15 y SHALL reemplazar la metadata fiscal heredada del documento fuente por valores canónicos de Factura obtenidos en servidor.

#### Scenario: Recepción con comprobante de guía

- **WHEN** una recepción autorizada contiene un `tipo_comprobante` distinto de Factura
- **THEN** el mapeador puede copiarlo al documento en memoria
- **AND** el adaptador lo reemplaza por el registro de Factura con código SUNAT `01` antes de insertar

#### Scenario: Identidad fiscal canónica

- **WHEN** el documento en memoria contiene valores fiscales heredados de la recepción
- **THEN** la factura recibe el tipo y código de identidad validados desde el Supplier y su catálogo

#### Scenario: Validación estricta fuera del flujo de recepción

- **WHEN** otro flujo presenta un valor fiscal actual distinto del catálogo y no habilita la sobrescritura interna
- **THEN** el sistema rechaza la inconsistencia

#### Scenario: Validación nativa fallida

- **WHEN** ERPNext o el catálogo fiscal rechazan la factura
- **THEN** la transacción no conserva el registro, la factura ni sus adjuntos
