## Why

Al mapear una Purchase Receipt a Purchase Invoice, ERPNext copia campos personalizados con el mismo nombre. En el sitio `v15.local`, `PREC-03486` contiene `tipo_comprobante = Guía de remisión - Remitente`; ese valor llega a la factura en memoria y el adaptador fiscal lo rechaza porque el destino debe ser `Factura`, código SUNAT `01`. La transacción se revierte correctamente, pero impide registrar una factura válida desde la recepción.

## What Changes

- Tratar los valores fiscales heredados por el mapeador de Purchase Receipt como metadata del documento fuente, no como valores fiscales de la factura destino.
- Permitir que el adaptador fiscal sobrescriba esos valores únicamente desde el flujo interno de Purchase Receipt.
- Mantener la validación estricta existente para el flujo desde Purchase Order y para cualquier otro llamador.
- Añadir pruebas unitarias y de integración que reproduzcan una recepción con un tipo de comprobante distinto de Factura.

## Scope

La corrección se limita al adaptador fiscal interno y a la creación de Purchase Invoice desde Purchase Receipt. No cambia payloads del navegador, DocTypes, permisos ni documentos existentes.

## Exclusions

- Cambiar catálogos SUNAT o datos de `PREC-03486`.
- Aceptar tipo de comprobante enviado por el proveedor.
- Relajar la validación fiscal del flujo desde Purchase Order.
- Modificar impuestos, importes, series, correlativos, XML o integración electrónica.
- Cambios en `apps/frappe` o `apps/erpnext`.

## Expected Impact

- Facturación: la Purchase Invoice creada desde una recepción usará siempre el registro canónico `Factura` con código `01`.
- Seguridad: los valores continúan derivándose en servidor desde catálogos y Supplier; el navegador no controla la sobrescritura.
- Base de datos: sin cambios de esquema, patches ni migración.
- Datos existentes: ninguno se modifica automáticamente.

## Acceptance Criteria

- Una recepción cuyo `tipo_comprobante` sea una guía puede generar una Purchase Invoice Draft.
- La factura resultante contiene `tipo_comprobante = Factura` y `codigo_comprobante = 01` desde el catálogo.
- La identidad fiscal resultante coincide con el Supplier y su catálogo.
- La sobrescritura solo se habilita desde el mapeador interno de Purchase Receipt.
- El adaptador continúa rechazando valores incompatibles cuando no se habilita esa sobrescritura.
- Una falla posterior revierte solicitud, factura y adjuntos como antes.
- OpenSpec, pruebas y validaciones estáticas finalizan correctamente.
