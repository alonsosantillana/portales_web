## MODIFIED Requirements

### Requirement: Sincronización del resultado

El sistema SHALL marcar la solicitud como Procesada cuando la Purchase Invoice sea enviada, SHALL marcarla como Rechazada cuando sea cancelada y SHALL retirar el vínculo sin eliminar la solicitud cuando la Purchase Invoice sea eliminada.

#### Scenario: Submit interno

- **WHEN** un usuario interno envía la Purchase Invoice
- **THEN** el registro relacionado cambia a Procesada y conserva el vínculo

#### Scenario: Cancelación interna

- **WHEN** un usuario interno cancela la Purchase Invoice
- **THEN** el registro relacionado cambia a Rechazada y conserva el vínculo

#### Scenario: Eliminación interna de la factura

- **WHEN** un usuario interno elimina una Purchase Invoice cancelada
- **THEN** el registro relacionado permanece, cambia a Rechazada y queda sin vínculo a esa factura

### Requirement: Eliminación ordenada de la solicitud

El sistema SHALL impedir eliminar una Supplier Invoice Submission mientras exista su Purchase Invoice vinculada y SHALL permitir la eliminación después de retirar el vínculo o cuando el documento vinculado ya no exista.

#### Scenario: Factura vinculada existente

- **WHEN** un usuario intenta eliminar una solicitud cuya Purchase Invoice todavía existe
- **THEN** el sistema bloquea la acción e indica cancelar si corresponde y eliminar primero la factura

#### Scenario: Solicitud desvinculada

- **WHEN** la Purchase Invoice fue eliminada y el hook retiró el vínculo
- **THEN** un usuario autorizado puede eliminar manualmente la solicitud

#### Scenario: Vínculo histórico inválido

- **WHEN** una solicitud conserva el nombre de una Purchase Invoice que ya no existe
- **THEN** el vínculo inválido no impide eliminar la solicitud
