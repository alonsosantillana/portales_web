## Why

Se necesita una aplicación Frappe independiente que sirva como base versionada y trazable para futuras funcionalidades de portales web. La inicialización debe establecer una estructura compatible con Frappe y ERPNext v15 sin incorporar todavía lógica de negocio no definida.

## What Changes

- Crear la aplicación técnica `portales_web` con título "Portales Web".
- Incluir la estructura estándar generada por Frappe para código, configuración, plantillas, recursos públicos y patches.
- Configurar metadatos básicos, licencia MIT y empaquetado Python editable administrado por Bench.
- Inicializar el repositorio Git y trabajar en la rama dedicada `feature/init-portales-web`.
- Inicializar OpenSpec y documentar la base funcional y técnica del proyecto.
- Preparar Graphify para análisis local de código con exclusiones seguras y artefactos no versionados.
- Validar la estructura Python, la configuración del paquete y la compilación de assets.

## Capabilities

### New Capabilities

- `app-foundation`: Base instalable de una aplicación Frappe v15 llamada `portales_web`, preparada para extensiones futuras mediante los mecanismos estándar del framework.

### Modified Capabilities

Ninguna.

## Scope

La tarea cubre la creación y validación de la base técnica de la app dentro de `apps/portales_web`, incluida la preparación local y aislada de Graphify.

## Exclusions

- Instalación en un sitio Frappe.
- Creación de DocTypes, Custom Fields, roles, permisos, workflows o fixtures.
- Implementación de APIs, integraciones, páginas web o lógica de negocio.
- Configuración de remoto Git, push o merge.
- Migraciones o modificaciones de datos.
- Integración MCP, hooks automáticos o análisis semántico mediante proveedores remotos.

## Expected Impact

El bench incorpora una nueva dependencia editable y enlaza sus recursos públicos. No se altera ningún sitio ni base de datos hasta que se autorice una instalación posterior.

## Acceptance Criteria

- Existe `apps/portales_web` con la estructura estándar de una app Frappe.
- Los metadatos identifican correctamente la app y declaran compatibilidad Python adecuada para Frappe v15.
- El repositorio se encuentra en una rama de trabajo dedicada y sin cambios ajenos.
- OpenSpec contiene propuesta, especificación, diseño y tareas válidas para esta inicialización.
- Graphify dispone de exclusiones seguras, documentación local y un grafo de código no versionado.
- Las validaciones de estructura, sintaxis y configuración finalizan correctamente.

## Impact

- Código: nueva app `portales_web`; no se modifica `frappe` ni `erpnext`.
- APIs y hooks: no se habilitan APIs ni hooks funcionales.
- Dependencias: registro editable de la app en el entorno Python del bench; sin dependencias externas nuevas.
- Herramientas: preparación local de Graphify; `graphify-out/` y el registro de consultas quedan excluidos de Git.
- Sistemas: assets del bench enlazados y compilados; `v15.local` permanece sin la app instalada.
