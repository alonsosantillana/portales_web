## ADDED Requirements

### Requirement: Reintento de solicitud rechazada

El sistema SHALL permitir reintentar una factura desde la misma Purchase Receipt reutilizando su solicitud cuando esta esté Rechazada y no tenga Purchase Invoice vinculada. El sistema SHALL bloquear y releer la solicitud, SHALL recalcular todas las validaciones y SHALL conservar la operación en una sola transacción.

#### Scenario: Reintento elegible

- **WHEN** existe la misma clave de Supplier y factura en una solicitud Rechazada, sin Purchase Invoice y de la misma Purchase Receipt
- **THEN** el sistema reutiliza el identificador de la solicitud
- **AND** revalida datos, disponibilidad, ítems, archivos y metadata fiscal
- **AND** crea una nueva Purchase Invoice Draft y deja la solicitud En revisión

#### Scenario: Reintentos concurrentes

- **WHEN** dos peticiones intentan reutilizar simultáneamente la misma solicitud
- **THEN** solo una puede cambiarla y crear la nueva Purchase Invoice
- **AND** la segunda observa el resultado actualizado como idempotente

#### Scenario: Solicitud no elegible

- **WHEN** la solicitud tiene vínculo, no está Rechazada o pertenece a otro origen o recepción
- **THEN** el sistema no la modifica y responde como factura ya registrada

#### Scenario: Falla durante el reintento

- **WHEN** falla cualquier validación o creación posterior a preparar la solicitud
- **THEN** la transacción restaura el estado y los datos previos

### Requirement: Respuesta de duplicado comprensible

El sistema SHALL distinguir visualmente entre un duplicado con Purchase Invoice y un registro sin factura vinculada.

#### Scenario: Duplicado sin Purchase Invoice

- **WHEN** una respuesta idempotente no contiene Purchase Invoice
- **THEN** la interfaz muestra el identificador y estado de la solicitud sin imprimir `null` ni afirmar que existe un borrador
