## 1. Especificación y modelo

- [x] 1.1 Analizar el mapeador nativo de Purchase Receipt, permisos web y componentes existentes con código y Graphify.
- [x] 1.2 Definir alcance, seguridad, concurrencia, riesgos y reversión en OpenSpec.
- [x] 1.3 Extender los DocTypes de auditoría con tipo y referencias de origen compatibles con registros existentes.

## 2. Servicios seguros

- [x] 2.1 Implementar consultas filtradas de Recepciones de Compra elegibles e ítems pendientes.
- [x] 2.2 Implementar validación y reserva transaccional por Purchase Receipt Item.
- [x] 2.3 Crear Purchase Invoice Draft mediante el motor nativo de mapeo y servicios compartidos.
- [x] 2.4 Actualizar el historial para identificar ambos tipos de origen.

## 3. Portal

- [x] 3.1 Crear la página autenticada `registrar-factura-recepcion` y su JavaScript.
- [x] 3.2 Añadir la opción `Facturar recepción` al menú del Supplier.
- [x] 3.3 Mantener enlaces claros entre los dos flujos y las facturas existentes.

## 4. Pruebas y validación

- [x] 4.1 Añadir pruebas de aislamiento, estados, devoluciones, cantidades y manipulación de ítems.
- [x] 4.2 Añadir y ejecutar pruebas de creación nativa, referencias, reservas, duplicados y archivos privados.
- [x] 4.3 Ejecutar regresión unitaria del flujo por Purchase Order y validaciones estáticas (21 pruebas OK).
- [x] 4.4 Migrar `v15.local` con autorización y ejecutar integración real/concurrencia.
- [x] 4.5 Regenerar Graphify, actualizar resultados y revisar Git.

## Resultados de validación

- `bench --site v15.local migrate`: completado correctamente.
- `bench --site v15.local run-tests --app portales_web`: 25 pruebas OK.
- Python `py_compile`, `node --check` y `git diff --check`: OK.
- HTTP Guest: nueva ruta redirige al login; asset JavaScript 200; endpoint protegido 403.
- Graphify local: 300 nodos y 393 relaciones; `graphify-out/` permanece ignorado.
- Graphify advirtió que los dos JSON de DocType no producen nodos; ambos fueron verificados directamente y validados como JSON.
