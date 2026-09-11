## ADDED Requirements

### Requirement: Retroalimentación durante el registro

El sistema SHALL mostrar una espera bloqueante y un mensaje de procesamiento mientras prepara y registra una factura desde Purchase Receipt, y SHALL impedir envíos duplicados hasta recibir un resultado.

#### Scenario: Inicio de procesamiento válido

- **WHEN** el usuario envía un formulario válido con cantidades, PDF y XML
- **THEN** la interfaz muestra inmediatamente “Procesando factura. Por favor, espere.”
- **AND** marca el formulario como ocupado y bloquea otro Submit

#### Scenario: Registro exitoso

- **WHEN** el servidor devuelve el resultado de la factura
- **THEN** la interfaz cierra la espera antes de mostrar el mensaje de éxito
- **AND** vuelve a habilitar el botón

#### Scenario: Error de lectura o servidor

- **WHEN** falla la lectura de un adjunto o la solicitud al servidor
- **THEN** la interfaz retira la espera, limpia el estado ocupado y vuelve a habilitar el botón

#### Scenario: Validación local incompleta

- **WHEN** faltan campos, cantidades positivas o adjuntos
- **THEN** la interfaz presenta el error local sin abrir la pantalla de espera
