## MODIFIED Requirements

### Requirement: Origen auditable y exclusivo

Cada Supplier Invoice Submission SHALL identificar un `source_type` y exactamente un documento de origen: Purchase Order o Purchase Receipt. Los registros históricos sin tipo SHALL conservar semántica de Purchase Order.

#### Scenario: Registro desde Orden de Compra

- **WHEN** se crea una solicitud desde el flujo existente
- **THEN** `source_type` es Purchase Order, `purchase_order` está informado y `purchase_receipt` está vacío

#### Scenario: Registro desde Recepción de Compra

- **WHEN** se crea una solicitud desde el nuevo flujo
- **THEN** `source_type` es Purchase Receipt, `purchase_receipt` está informado y el vínculo padre de Purchase Order no es obligatorio

### Requirement: Ítems auditables según origen

Cada ítem SHALL conservar la referencia del child del origen correspondiente y snapshots de cantidades calculadas en servidor.

#### Scenario: Ítem de recepción

- **WHEN** se registra una cantidad desde una Purchase Receipt
- **THEN** el child almacena `purchase_receipt_item`, artículo, unidad, saldo, cantidad, tarifa e importe
