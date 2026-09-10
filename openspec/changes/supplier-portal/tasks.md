## 1. Modelo y permisos

- [x] 1.1 Crear `Supplier Invoice Submission` con auditoría, identidad única, estado, totales, adjuntos y vínculo a Purchase Invoice.
- [x] 1.2 Crear `Supplier Invoice Submission Item` con referencias y snapshots de cantidades calculadas por servidor.
- [x] 1.3 Configurar permisos internos sin otorgar a Supplier creación o edición directa sobre Purchase Invoice ni el registro intermedio.

## 2. Servicios seguros

- [x] 2.1 Implementar resolución de un único Supplier efectivo mediante Portal User y rol Supplier.
- [x] 2.2 Implementar consultas filtradas de OCs elegibles, ítems pendientes y registros propios.
- [x] 2.3 Implementar normalización, duplicados, idempotencia y validación de cantidades con reservas activas.
- [x] 2.4 Implementar validación y almacenamiento privado de PDF/XML.
- [x] 2.5 Crear Purchase Invoice Draft mediante el mapeador nativo dentro de la misma transacción.
- [x] 2.6 Implementar enriquecimiento fiscal condicional desde Supplier y catálogos Ovenube para el comprobante SUNAT `01`.

## 3. Portal y estados

- [x] 3.1 Crear página autenticada `registrar-factura` con carga de OC, cantidades, datos de factura y archivos.
- [x] 3.2 Añadir el menú del portal para el rol Supplier.
- [x] 3.3 Sincronizar estados al enviar, cancelar o eliminar la Purchase Invoice.

## 4. Pruebas y validación

- [x] 4.1 Añadir pruebas unitarias aisladas de identidad, separación entre Suppliers y manipulación de OC/ítems.
- [x] 4.2 Añadir pruebas unitarias de cantidades parciales, valores controlados por servidor y validación de archivos.
- [x] 4.3 Ejecutar en un sitio de pruebas la creación Draft, reserva parcial, duplicados/idempotencia, archivos privados y enriquecimiento fiscal.
- [x] 4.6 Ejecutar una prueba multi-conexión de concurrencia y el ciclo real Submit/Cancel antes de promover a producción.
- [x] 4.4 Ejecutar validaciones estáticas y las pruebas disponibles sin migrar sitios no autorizados.
- [x] 4.5 Regenerar Graphify, verificar Git/OpenSpec y documentar pruebas pendientes de sitio.

## Validación del sitio

- [x] Instalar `portales_web` en `v15.local`.
- [x] Ejecutar `bench --site v15.local migrate`.
- [x] Verificar creación de ambos DocTypes, redirección de Guest y bloqueo anónimo de la API.
- [x] Completar la prueba end-to-end después de implementar el adaptador fiscal aprobado.
