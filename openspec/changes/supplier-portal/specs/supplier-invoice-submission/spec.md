## Purpose

Permitir que un proveedor registre de forma auditable e idempotente los datos y documentos privados de su factura contra una Orden de Compra autorizada.

## ADDED Requirements

### Requirement: Datos controlados por servidor

El sistema MUST ignorar cualquier Supplier, Company, Currency, Item, Rate, Amount o estado recibido del navegador y SHALL reconstruir esos valores desde la Orden de Compra validada.

#### Scenario: Manipulación de datos derivados

- **WHEN** el navegador envía valores derivados distintos de los almacenados en ERPNext
- **THEN** el servidor utiliza los valores de ERPNext y no los valores manipulados

### Requirement: Identidad única de factura

El sistema SHALL normalizar el número de factura y SHALL mantener una clave única por Supplier para impedir registros duplicados y reintentos que creen documentos adicionales.

#### Scenario: Factura duplicada

- **WHEN** existe una solicitud o Purchase Invoice activa con el mismo Supplier y número normalizado
- **THEN** el sistema rechaza un nuevo registro y devuelve una referencia segura al registro existente cuando pertenece al mismo usuario

### Requirement: Adjuntos privados obligatorios

El sistema SHALL exigir un PDF válido y un XML válido, SHALL respetar el límite global de archivos y MUST almacenarlos como archivos privados.

#### Scenario: Archivos válidos

- **WHEN** el proveedor envía un PDF con firma de archivo PDF y un XML con contenido textual XML dentro del tamaño permitido
- **THEN** ambos archivos se almacenan como privados y quedan asociados a la factura creada

#### Scenario: Archivo inválido

- **WHEN** la extensión, firma, codificación o tamaño no cumple las reglas
- **THEN** la operación se rechaza sin crear una Purchase Invoice

### Requirement: Estados auditables

El sistema SHALL registrar cambios y SHALL exponer al proveedor los estados Registrada, En revisión, Observada, Procesada o Rechazada sin permitir que el proveedor los establezca directamente.

#### Scenario: Consulta de estado

- **WHEN** el proveedor consulta sus registros
- **THEN** recibe el estado y la Purchase Invoice asociada únicamente para su Supplier
