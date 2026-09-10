## Purpose

Definir la base observable y segura de `portales_web` como aplicación independiente, identificable e instalable en un entorno compatible con Frappe v15.

## ADDED Requirements

### Requirement: Identidad de la aplicación

La aplicación SHALL identificarse técnicamente como `portales_web` y SHALL exponer el título "Portales Web", una descripción, un publicador, un correo de contacto y una licencia mediante sus metadatos de paquete y hooks.

#### Scenario: Inspección de metadatos

- **WHEN** una herramienta compatible inspecciona el paquete o los hooks de la aplicación
- **THEN** encuentra una identidad coherente para `portales_web` y la licencia MIT

### Requirement: Estructura instalable de Frappe

La aplicación SHALL conservar la estructura mínima reconocida por Frappe v15 para módulos, hooks, patches, plantillas y recursos públicos, y SHALL poder registrarse como paquete Python editable administrado por Bench.

#### Scenario: Registro en el entorno del bench

- **WHEN** Bench registra la aplicación desde su directorio fuente
- **THEN** el paquete queda disponible en el entorno Python sin requerir dependencias externas adicionales

#### Scenario: Compilación de recursos

- **WHEN** Bench ejecuta la compilación de assets para `portales_web`
- **THEN** reconoce la aplicación y termina sin errores atribuibles a su estructura inicial

### Requirement: Aislamiento respecto de los sitios

La creación de la base de la aplicación MUST mantener sin cambios la configuración y los datos de los sitios existentes hasta recibir una autorización explícita de instalación.

#### Scenario: App creada sin instalación

- **WHEN** finaliza la inicialización del proyecto
- **THEN** `portales_web` existe en el bench pero no aparece como aplicación instalada en `v15.local`

### Requirement: Trazabilidad del proyecto

La aplicación SHALL mantener su inicialización en una rama Git dedicada y SHALL incluir artefactos OpenSpec válidos que documenten alcance, diseño y tareas.

#### Scenario: Revisión de trazabilidad

- **WHEN** se revisa el repositorio de `portales_web`
- **THEN** la rama activa es `feature/init-portales-web` y el cambio `init-portales-web` puede validarse con OpenSpec

### Requirement: Análisis estructural local seguro

La aplicación SHALL proporcionar reglas y documentación para generar un grafo Graphify limitado a código local, excluyendo secretos, sitios, archivos privados, respaldos, logs, documentos y artefactos generados.

#### Scenario: Extracción local del código

- **WHEN** se ejecuta Graphify desde la raíz de `portales_web` con el modo `--code-only --no-cluster` y el registro de consultas deshabilitado
- **THEN** el grafo se genera en `graphify-out/` sin requerir un proveedor remoto de IA

#### Scenario: Revisión del estado Git

- **WHEN** Graphify ha generado sus artefactos locales
- **THEN** `graphify-out/` y el registro local de consultas permanecen excluidos del repositorio Git
