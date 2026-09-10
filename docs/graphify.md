# Graphify local para portales_web

Graphify se usa exclusivamente desde la raíz de esta app para consultar relaciones estructurales del código. No reemplaza OpenSpec ni la revisión directa de hooks, DocTypes, fixtures y configuración Frappe.

## Generar o actualizar el grafo

Ejecutar desde `apps/portales_web`:

```bash
GRAPHIFY_QUERY_LOG_DISABLE=1 graphify extract . --code-only --no-cluster
```

Para actualizar un grafo existente sin análisis semántico remoto:

```bash
GRAPHIFY_QUERY_LOG_DISABLE=1 graphify update . --no-cluster
```

El resultado se genera en `graphify-out/` y no debe versionarse.

## Consultas locales

```bash
GRAPHIFY_QUERY_LOG_DISABLE=1 graphify god-nodes --graph graphify-out/graph.json
GRAPHIFY_QUERY_LOG_DISABLE=1 graphify explain "portales_web" --graph graphify-out/graph.json
GRAPHIFY_QUERY_LOG_DISABLE=1 graphify affected "portales_web" --graph graphify-out/graph.json
```

Las conclusiones deben verificarse contra el código fuente y la configuración real antes de modificar la app.

## Restricciones

- No ejecutar Graphify desde la raíz de `frappe-bench`.
- No usar `graphify install`, `graphify codex install` ni `graphify hook install`.
- No habilitar análisis de PDFs, imágenes, URLs, Google Workspace, bases de datos o Pull Requests.
- No usar proveedores remotos de IA sin autorización explícita.
- No exponer el grafo mediante HTTP; una futura integración MCP debe usar `stdio` y requiere autorización por separado.
- No incluir sitios, respaldos, logs, claves, certificados, credenciales ni archivos de clientes.
