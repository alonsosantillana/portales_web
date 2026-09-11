## Context

`supplier_receipt_invoice_portal.js` maneja el evento Submit, deshabilita el botón y espera la lectura de archivos, la API y la recarga de listas. La página Frappe ya carga `frappe-web.bundle.js`, que incluye `frappe.dom.freeze` y `frappe.dom.unfreeze`; por tanto no se necesita markup, CSS ni una dependencia adicional.

Graphify ubica el envío en `supplier_receipt_invoice_portal.js` y confirma su relación con `submit_invoice_from_receipt`. La revisión directa muestra que el cambio puede permanecer completamente en cliente.

## Goals / Non-Goals

**Goals:**

- Dar retroalimentación inmediata y visible durante el envío.
- Impedir dobles envíos por clic o Submit repetido.
- Garantizar limpieza del overlay en éxito y error.
- Reutilizar el mecanismo visual soportado por Frappe v15.

**Non-Goals:**

- Estimar avance porcentual.
- Cambiar tiempos o etapas del procesamiento de servidor.
- Modificar el portal por Orden de Compra sin una solicitud separada.

## Decisions

### Usar el bloqueo nativo de Frappe

Se usará `frappe.dom.freeze` con un mensaje traducible y `frappe.dom.unfreeze` para conservar la apariencia estándar, bloquear la interacción y evitar CSS propio.

### Iniciar después de validaciones locales

El overlay se activa después de `reportValidity`, la validación de cantidades y la presencia de PDF/XML. Los errores locales permanecen inmediatos y no generan parpadeos.

### Limpieza idempotente

Una función de estado administrará botón, `aria-busy`, bandera de envío y freeze. La salida exitosa cerrará la espera antes de abrir `frappe.msgprint`; el bloque `finally` garantizará la limpieza ante errores y será seguro si ya se limpió.

## Affected Components

- JavaScript: `portales_web/public/js/supplier_receipt_invoice_portal.js`.
- APIs, DocTypes, hooks, HTML, CSS, reportes, fixtures y core: sin cambios.

## Risks / Trade-offs

- [Overlay no retirado por excepción] → Limpieza centralizada dentro de `finally`.
- [Dos submits por teclado o doble clic] → Bandera local además del botón deshabilitado.
- [Conflicto con otro freeze] → Cada activación propia incrementa una vez y la limpieza idempotente decrementa una vez.

## Migration and Rollback

No requiere migración ni restart por esquema. La reversión elimina la función de estado y restaura el deshabilitado simple del botón.
