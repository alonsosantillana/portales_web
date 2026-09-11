## Why

El registro de una factura desde Purchase Receipt valida datos, procesa dos archivos y crea documentos en servidor. Durante ese intervalo el botón solo queda deshabilitado y el usuario no recibe una señal visible de que la operación continúa, lo que puede generar incertidumbre o intentos repetidos.

## What Changes

- Mostrar el bloqueo visual nativo de Frappe inmediatamente después de validar el formulario y antes de leer los adjuntos.
- Informar “Procesando factura. Por favor, espere.” durante toda la solicitud.
- Marcar el formulario como ocupado y bloquear envíos duplicados.
- Retirar la espera antes de presentar el resultado exitoso y también ante cualquier error.

## Scope

La mejora se limita al botón `Registrar factura` de la página `registrar-factura-recepcion` solicitada por el usuario.

## Exclusions

- Cambios al flujo desde Purchase Order.
- Indicadores de porcentaje o progreso del servidor.
- Cambios en APIs, lógica contable, DocTypes, archivos o base de datos.

## Expected Impact

- Experiencia: el usuario recibe confirmación inmediata y no puede duplicar el envío mientras se procesa.
- Accesibilidad: el formulario expone `aria-busy` durante la operación.
- Backend y datos: sin impacto.

## Acceptance Criteria

- La espera aparece únicamente después de que los datos obligatorios, cantidades y adjuntos pasan la validación del navegador.
- El mensaje permanece visible mientras se leen archivos y se espera la respuesta del servidor.
- Un segundo submit es ignorado mientras el primero sigue activo.
- La espera desaparece antes del mensaje de éxito.
- La espera y el estado ocupado se limpian cuando ocurre un error.
- El botón vuelve a estar disponible al terminar.
- JavaScript, OpenSpec y pruebas existentes validan correctamente.
