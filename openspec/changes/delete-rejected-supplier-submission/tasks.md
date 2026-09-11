## 1. Trazabilidad y diseño

- [x] 1.1 Confirmar rama principal, estado Git, OpenSpec, Graphify, controlador y hooks afectados.
- [x] 1.2 Documentar alcance, orden de eliminación, riesgos y reversión.
- [x] 1.3 Validar el cambio OpenSpec en modo estricto.

## 2. Implementación

- [x] 2.1 Mantener el bloqueo mientras exista la Purchase Invoice y mejorar el mensaje de acción.
- [x] 2.2 Permitir limpiar una solicitud con vínculo histórico inexistente.
- [x] 2.3 Desvincular y marcar Rechazada la solicitud al eliminar la Purchase Invoice, sin cascada.

## 3. Pruebas y cierre

- [x] 3.1 Añadir pruebas unitarias del bloqueo y de los eventos Submit, Cancel y Trash.
- [x] 3.2 Verificar el ciclo real cancelar/eliminar factura y eliminar solicitud en el sitio de pruebas.
- [x] 3.3 Ejecutar pruebas, validaciones estáticas y `git diff --check`.
- [x] 3.4 Regenerar Graphify, revisar estado/diff y documentar resultados.

## Validation Record

- `openspec validate delete-rejected-supplier-submission --strict`: válido.
- Compilación Python de controlador y pruebas: correcta.
- Pruebas unitarias: 18 pruebas correctas, incluidos Submit, Cancel, Trash, bloqueo y vínculo histórico inválido.
- Pruebas de integración: 2 pruebas correctas; verifican Cancel, eliminación de Purchase Invoice, desvinculado y eliminación manual de la solicitud.
- Suite completa de la app: 20 pruebas correctas en 61.003 segundos.
- `graphify update . --no-cluster`: grafo local regenerado con 254 nodos y 309 relaciones; artefactos ignorados por Git.
- `git diff --check`: sin errores.

## Deviations

Ninguna.
