### Portales Web

Aplicación Frappe para la gestión de portales web.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app portales_web
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/portales_web
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit

## Navegación en Frappe v16

La pantalla **Apps** muestra **Portales Web** para usuarios internos autorizados y
abre el DocType existente **Supplier Invoice Submission** (`/desk/supplier-invoice-submission`). El acceso
respeta los permisos actuales y las restricciones de módulo; no asigna roles.
El Dock estándar se importa de forma nativa al instalar/migrar esta app en v16.
No requiere crear Desktop Icons ni Workspace Sidebar, ni reconstruir assets.
Los iconos de Apps usan las iniciales nativas cuando no hay logo propio.

Alcance, activación puntual en desarrollo y reversión:
[OpenSpec show-apps-on-v16-desktop](openspec/changes/show-apps-on-v16-desktop/design.md).
Esta navegación exige el contrato Apps/Dock de v16; no modifica procesos de negocio.
