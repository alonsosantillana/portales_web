## 1. Análisis y trazabilidad

- [x] 1.1 Confirmar el estado real de `SIS-2026-09485` y la respuesta `null`.
- [x] 1.2 Consultar Graphify y confirmar el flujo contra API, controlador y pruebas.
- [x] 1.3 Documentar elegibilidad, concurrencia, auditoría, riesgos y reversión.
- [x] 1.4 Validar OpenSpec en modo estricto.

## 2. Implementación

- [x] 2.1 Ampliar la lectura idempotente con origen y crear validación de reintento.
- [x] 2.2 Bloquear y releer la solicitud antes de reutilizarla.
- [x] 2.3 Preparar el mismo documento con datos e ítems revalidados y completar el flujo existente.
- [x] 2.4 Mostrar un mensaje de duplicado sin `null` cuando no exista Purchase Invoice.

## 3. Pruebas y cierre

- [x] 3.1 Añadir pruebas unitarias de elegibilidad, bloqueo y rechazo de combinaciones no válidas.
- [x] 3.2 Extender la integración con eliminar Purchase Invoice y reintentar el mismo recibo/número.
- [x] 3.3 Ejecutar suite completa, OpenSpec y validaciones estáticas.
- [x] 3.4 Regenerar Graphify y revisar estado/diff final.

## Validation Record

- `openspec validate retry-rejected-receipt-invoice --strict`: válido.
- `python3 -m py_compile`: válido para API y pruebas modificadas.
- `node --check`: válido para el JavaScript modificado.
- `git diff --check`: sin errores.
- Integración específica: 5 pruebas aprobadas en 53.960 s.
- Suite completa: 36 pruebas aprobadas en 53.140 s.
- Graphify regenerado localmente: 416 nodos y 507 aristas; `graphify-out/` permanece ignorado.

## Deviations

- La serie del sitio puede reutilizar el identificador de una Purchase Invoice eliminada; la prueba valida existencia y `docstatus = 0` en lugar de exigir un nombre distinto.
- Una ejecución intermedia de la suite reveló que una prueba de bloqueo podía seleccionar datos no confirmados de otra prueba; el fixture se hizo determinista seleccionando desde la conexión secundaria y bloqueando explícitamente desde la primaria.
