## Context

La app fue creada con el generador estándar incluido en Frappe v15.109.0 dentro de un bench que contiene varias aplicaciones con repositorios independientes. El bench no es un repositorio Git; `portales_web` sí lo es y su rama inicial protegida fue `develop`. Véase `proposal.md` para la motivación y `specs/app-foundation/spec.md` para el contrato observable.

Graphify se prepara de forma aislada para esta app. Su uso inicial se limita al análisis AST local del código, sin proveedores remotos, documentos no estructurados, bases de datos ni fuentes externas.

## Goals / Non-Goals

**Goals:**

- Conservar la estructura convencional producida por Frappe para reducir mantenimiento y facilitar futuras extensiones.
- Separar la inicialización en `feature/init-portales-web` y documentarla mediante OpenSpec.
- Mantener el proyecto inerte respecto de sitios y bases de datos hasta una instalación autorizada.
- Permitir análisis estructural local mediante Graphify sin versionar artefactos generados.

**Non-Goals:**

- Diseñar el dominio funcional de los portales.
- Activar hooks, endpoints, jobs, permisos o modelos de datos.
- Añadir dependencias o configuración operativa del bench.
- Configurar MCP, hooks Git, integración con agentes o análisis semántico remoto de Graphify.

## Decisions

### Usar el generador estándar de Bench

Se usa `bench new-app portales_web` para obtener la estructura soportada por Frappe v15 y registrar el paquete de forma editable. La alternativa de construir archivos manualmente se descarta porque aumenta el riesgo de omitir convenciones o pasos internos del framework.

### Mantener la plantilla de hooks sin activaciones funcionales

`portales_web/hooks.py` conserva los puntos de extensión comentados que genera Frappe. No se activan hooks hasta que una especificación funcional defina su comportamiento. La alternativa de eliminar la plantilla reduce ruido, pero también pierde una referencia estándar útil para la evolución del proyecto.

### Separar creación e instalación

La app se crea y compila, pero no se instala en `v15.local`. Esto evita migraciones y efectos sobre datos antes de acordar el sitio y las primeras capacidades. Instalarla inmediatamente se descarta por requerir autorización independiente y una validación de impacto sobre el sitio.

### Ejecutar OpenSpec con Node.js 20 de forma localizada

La CLI OpenSpec 1.7.0 usa una expresión regular no soportada por el Node.js 18 activo. Se invoca con el binario Node.js 20.20.2 ya presente mediante un ajuste temporal de `PATH`, sin cambiar la versión global del bench.

### Preparar Graphify en modo local y aislado

Se incorpora `.graphifyignore`, se excluye `graphify-out/` de Git y se documenta la extracción `--code-only --no-cluster` con `GRAPHIFY_QUERY_LOG_DISABLE=1`. Esta modalidad usa análisis AST local y evita enviar contenido a proveedores de IA. Se descartan `graphify install`, integraciones automáticas, hooks, HTTP y MCP porque modifican otras superficies o requieren autorización específica.

## Affected Components

- DocTypes: ninguno.
- Hooks: `portales_web/hooks.py`, solo metadatos y plantilla inactiva.
- APIs: ninguna.
- Reportes: ninguno.
- Fixtures: ninguno.
- Archivos de aplicación: `pyproject.toml`, `README.md`, `license.txt`, `portales_web/modules.txt`, `portales_web/patches.txt`, módulos Python, plantillas y recursos públicos generados.
- Trazabilidad: `openspec/config.yaml` y `openspec/changes/init-portales-web/`.
- Graphify: `.graphifyignore`, `.gitignore`, `docs/graphify.md` y artefactos locales ignorados en `graphify-out/`.

## Risks / Trade-offs

- [Correo de contacto provisional `desarrollo@example.com`] → Sustituirlo mediante un cambio documental autorizado cuando se disponga del correo definitivo.
- [La app aún no está instalada en un sitio] → Validar instalación, migración y permisos en una tarea separada con autorización explícita.
- [OpenSpec no funciona con el Node.js 18 activo] → Ejecutar sus comandos con Node.js 20.20.2 mediante `PATH` local y documentar esta condición.
- [No existe remoto Git] → Configurar y hacer push solo cuando el usuario proporcione o autorice el repositorio destino.
- [Un grafo inicial pequeño aporta contexto limitado] → Regenerarlo después de incorporar estructura funcional relevante.
- [Inclusión accidental de datos sensibles] → Aplicar `.graphifyignore`, usar `--code-only` y revisar el alcance antes de cada extracción.

## Migration Plan

La inicialización no modifica esquemas ni datos, por lo que no requiere migración. Una instalación futura deberá ejecutarse de forma separada con `bench --site <sitio> install-app portales_web`, seguida de validaciones del sitio y con autorización explícita.

Para revertir antes de una instalación, se puede retirar la app del bench y su registro editable; esta operación es destructiva y solo debe realizarse con autorización. Después de instalarla, la reversión deberá evaluar datos y dependencias antes de usar `uninstall-app`.
