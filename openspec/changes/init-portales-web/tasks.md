## 1. Inicialización del proyecto

- [x] 1.1 Crear `portales_web` con el generador estándar de Frappe y metadatos básicos.
- [x] 1.2 Verificar que el paquete editable y la compilación inicial de assets finalicen correctamente.
- [x] 1.3 Crear la rama Git dedicada `feature/init-portales-web` a partir de `develop`.

## 2. Trazabilidad

- [x] 2.1 Inicializar OpenSpec dentro del repositorio de la app.
- [x] 2.2 Documentar propuesta, especificación y diseño para la capacidad `app-foundation`.
- [x] 2.3 Validar el cambio `init-portales-web` con OpenSpec en modo estricto.

## 3. Validación y cierre

- [x] 3.1 Validar sintaxis Python y metadatos del paquete.
- [x] 3.2 Confirmar que `portales_web` no fue instalada en `v15.local`.
- [x] 3.3 Revisar archivos creados, estado Git y resumen del diff.

## Validation Record

- `bench new-app portales_web`: completado; registro editable y compilación inicial de assets correctos.
- `openspec validate init-portales-web --strict`: cambio válido; 4/4 artefactos completos.
- Compilación en memoria de archivos Python: 7 archivos sin errores de sintaxis.
- Lectura de `pyproject.toml`: nombre y versión mínima de Python correctos.
- `bench --site v15.local list-apps`: `portales_web` no está instalada.
- `git diff --check`: sin errores de espacios en los archivos versionados.
- `graphify extract . --code-only --no-cluster`: grafo local generado con 8 nodos y 0 relaciones, sin análisis remoto.
- `graphify diagnose multigraph`: grafo consistente, sin nodos no verificados ni relaciones inválidas.
- `git check-ignore`: `graphify-out/graph.json` y `.graphify_query_log.jsonl` están excluidos de Git.

## Deviations

- OpenSpec se ejecuta con Node.js 20.20.2 mediante un `PATH` temporal porque la versión 1.7.0 no es compatible con el Node.js 18.20.8 activo del bench.

## 4. Preparación de Graphify

- [x] 4.1 Crear `.graphifyignore` con exclusiones de secretos, sitios, datos privados, respaldos, logs y artefactos generados.
- [x] 4.2 Excluir `graphify-out/` y el registro local de consultas mediante `.gitignore`.
- [x] 4.3 Documentar generación, actualización, consultas y restricciones en `docs/graphify.md`.
- [x] 4.4 Generar el grafo inicial en modo local `--code-only --no-cluster` con el registro de consultas deshabilitado.
- [x] 4.5 Verificar los artefactos generados, confirmar que Git los ignora y revalidar OpenSpec.
