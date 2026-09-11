## 1. Análisis y trazabilidad

- [x] 1.1 Reproducir conceptualmente el valor heredado y verificar `PREC-03486`, el catálogo y el campo Link.
- [x] 1.2 Consultar Graphify y confirmar la ruta contra el código real.
- [x] 1.3 Documentar alcance, seguridad, riesgo tributario y reversión.
- [x] 1.4 Validar OpenSpec en modo estricto.

## 2. Implementación

- [x] 2.1 Añadir sobrescritura fiscal explícita y deshabilitada por defecto.
- [x] 2.2 Activarla únicamente al crear Purchase Invoice desde Purchase Receipt.
- [x] 2.3 Mantener intacta la validación estricta del flujo desde Purchase Order.

## 3. Pruebas y cierre

- [x] 3.1 Añadir pruebas unitarias de sobrescritura controlada y rechazo estricto.
- [x] 3.2 Reproducir en integración una recepción con comprobante distinto de Factura.
- [x] 3.3 Ejecutar suite completa y validaciones Python, JavaScript, OpenSpec y Git.
- [x] 3.4 Regenerar Graphify y revisar el diff final.

## Validation Record

- Diagnóstico de sitio: `PREC-03486` usa `Guía de remisión - Remitente`; el catálogo canónico de factura es `Factura / 01`.
- `openspec validate fix-receipt-fiscal-metadata --strict`: válido.
- Pruebas unitarias: 28 correctas.
- Pruebas de integración: 4 correctas; el escenario SUNAT `09` se transforma a Factura `01`.
- Suite completa: 32 pruebas correctas en 30.327 segundos.
- Compilación Python y `git diff --check`: correctos.
- `graphify update . --no-cluster`: grafo local regenerado con 374 nodos y 463 relaciones; artefactos ignorados por Git.

## Deviations

Ninguna.
