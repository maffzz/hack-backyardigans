# Configuración de Notificaciones por Email con SNS

## Resumen

Se ha implementado un sistema de notificaciones asíncronas por email usando AWS SNS que envía correos según la **urgencia** del incidente:

- **ALTA**: Envía email urgente con 🚨
- **MEDIA**: Envía email con ⚠️
- **BAJA**: No envía email

## Arquitectura

1. **`createIncident.py`**: Al crear un incidente, invoca de forma asíncrona la función de email
2. **`common/email.py`**: Módulo que invoca la Lambda de notificaciones
3. **`notifications/sendEmailNotification.py`**: Lambda que envía el email usando SNS
4. **SNS Topic**: Topic configurado en `serverless.yml` para enviar emails

## Configuración

### 1. Desplegar el backend

```bash
cd backend
serverless deploy
```

Esto creará:
- El Topic SNS: `alertautec-backend-incident-notifications-dev`
- La Lambda: `alertautec-backend-dev-sendEmailNotification`

### 2. Suscribir email a SNS

**Opción A: Desde AWS Console**
1. Ir a **SNS → Topics**
2. Seleccionar el topic `alertautec-backend-incident-notifications-dev`
3. Click en **Create subscription**
4. Protocolo: **Email**
5. Endpoint: Tu email (ej: `admin@utec.edu.pe`)
6. Click **Create subscription**
7. **IMPORTANTE**: Revisar tu correo y confirmar la suscripción (click en el link de confirmación)

**Opción B: Desde CLI**
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:096410127560:alertautec-backend-incident-notifications-dev \
  --protocol email \
  --notification-endpoint admin@utec.edu.pe
```

Luego confirmar desde el email recibido.

### 3. Verificar permisos IAM

Asegúrate de que el role IAM (`LabRole`) tenga permisos para SNS:

```json
{
  "Effect": "Allow",
  "Action": [
    "sns:Publish"
  ],
  "Resource": "arn:aws:sns:us-east-1:*:alertautec-backend-incident-notifications-*"
}
```

## Flujo de Funcionamiento

1. Usuario crea incidente con `urgencia: "ALTA"` o `"MEDIA"`
2. `createIncident.py` guarda el incidente en DynamoDB
3. Se invoca `notify_incident_created()` para WebSocket (tiempo real)
4. Se invoca `notify_incident_by_email()` de forma asíncrona
5. La Lambda `sendEmailNotification` recibe el evento
6. Se publica mensaje en SNS Topic
7. SNS envía email al suscriptor confirmado

## Prueba

Crear un incidente con urgencia ALTA:

```bash
curl -X POST https://tu-api/student/incidents \
  -H "Authorization: tu-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "EMERGENCIA",
    "descripcion": "Prueba de notificación",
    "ubicacion": {"edificio": "Edificio 1", "piso": 1},
    "urgencia": "ALTA"
  }'
```

Deberías recibir un email en la dirección suscrita.

## Notas

- Los emails se envían de forma **asíncrona**, no bloquean la creación del incidente
- Solo se envían emails para urgencias **ALTA** y **MEDIA**
- El email incluye: ID, tipo, descripción, ubicación, reporter y fecha
- Para agregar más emails, crea más suscripciones en el Topic SNS

