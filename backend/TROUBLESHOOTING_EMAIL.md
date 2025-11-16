# Troubleshooting: Notificaciones por Email

## Problema: No recibo emails al crear incidentes

Sigue estos pasos para diagnosticar el problema:

### 1. Verificar que las variables de entorno estén configuradas

**Ejecuta:**
```bash
cd backend
serverless deploy
```

Esto asegura que las variables de entorno (`SERVICE_NAME`, `SNS_TOPIC_ARN`, `AWS_REGION`) estén configuradas en las Lambdas.

### 2. Verificar que la suscripción de SNS esté CONFIRMADA

**IMPORTANTE**: Solo recibirás emails si la suscripción está confirmada.

**Desde AWS Console:**
1. Ve a **SNS → Topics**
2. Selecciona `alertautec-backend-incident-notifications-dev`
3. Click en **Subscriptions**
4. Verifica el estado de tu suscripción:
   - ✅ **Confirmed** = Recibirás emails
   - ⚠️ **PendingConfirmation** = Revisa tu correo y confirma

**Si está pendiente:**
- Revisa tu bandeja de entrada (y spam) del email que suscribiste
- Busca un email de AWS SNS con el asunto "AWS Notification - Subscription Confirmation"
- Click en el link de confirmación

**Desde CLI:**
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:096410127560:alertautec-backend-incident-notifications-dev
```

### 3. Verificar permisos IAM

El role `LabRole` debe tener permisos para publicar en SNS:

**Verificar permisos:**
```bash
aws iam get-role-policy \
  --role-name LabRole \
  --policy-name <nombre-de-politica>
```

**Si no tiene permisos, agrega esta política al role `LabRole`:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:us-east-1:096410127560:alertautec-backend-incident-notifications-dev"
    }
  ]
}
```

O desde AWS Console:
1. IAM → Roles → LabRole
2. Agregar política inline o attach policy
3. Permiso: `sns:Publish` en el ARN del topic

### 4. Verificar logs de CloudWatch

**Logs de createIncident:**
```bash
aws logs tail /aws/lambda/alertautec-backend-dev-createIncident --follow
```

Busca mensajes como:
- `"Notificación por email invocada"` = ✅ La función se invocó
- `"Error invocando notificación por email"` = ❌ Hay un error

**Logs de sendEmailNotification:**
```bash
aws logs tail /aws/lambda/alertautec-backend-dev-sendEmailNotification --follow
```

Busca:
- `"Email enviado exitosamente. MessageId: ..."` = ✅ Email enviado a SNS
- `"Error: SNS_TOPIC_ARN no configurado"` = ❌ Falta variable de entorno
- `"Error enviando email: ..."` = ❌ Error al publicar en SNS

### 5. Probar la función directamente

Usa el script de prueba:

```bash
cd backend
python test_email_notification.py
```

O invoca manualmente:

```bash
aws lambda invoke \
  --function-name alertautec-backend-dev-sendEmailNotification \
  --payload '{
    "incident": {
      "incident_id": "test-123",
      "tipo": "EMERGENCIA",
      "descripcion": "Prueba",
      "ubicacion": {"edificio": "Edificio 1"},
      "urgencia": "ALTA",
      "created_at": "2024-01-01T00:00:00"
    },
    "reporter_email": "test@utec.edu.pe"
  }' \
  response.json

cat response.json
```

### 6. Verificar que el incidente tenga urgencia ALTA o MEDIA

**IMPORTANTE**: Solo se envían emails para urgencias **ALTA** o **MEDIA**.

Al crear un incidente, asegúrate de que:
```json
{
  "urgencia": "ALTA"  // o "MEDIA"
}
```

Si usas `"urgencia": "BAJA"`, **NO se enviará email** (es el comportamiento esperado).

### 7. Verificar el Topic SNS

**Verificar que el topic existe:**
```bash
aws sns list-topics | grep incident-notifications
```

**Ver el ARN completo:**
```bash
aws sns list-topics --query "Topics[?contains(TopicArn, 'incident-notifications')]"
```

**Verificar suscripciones:**
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:096410127560:alertautec-backend-incident-notifications-dev
```

### 8. Checklist rápido

- [ ] ¿Ejecutaste `serverless deploy` después de agregar las variables de entorno?
- [ ] ¿La suscripción de SNS está **CONFIRMADA** (no pendiente)?
- [ ] ¿El role IAM tiene permisos `sns:Publish`?
- [ ] ¿El incidente tiene `urgencia: "ALTA"` o `"MEDIA"`?
- [ ] ¿Revisaste los logs de CloudWatch?
- [ ] ¿El Topic SNS existe y tiene el nombre correcto?

### 9. Solución rápida: Re-suscribir email

Si nada funciona, intenta re-suscribir tu email:

```bash
# Eliminar suscripción anterior (si existe)
aws sns unsubscribe --subscription-arn <arn-de-suscripcion>

# Crear nueva suscripción
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:096410127560:alertautec-backend-incident-notifications-dev \
  --protocol email \
  --notification-endpoint tu-email@utec.edu.pe
```

Luego confirma desde el email recibido.

## Errores comunes

### Error: "SNS_TOPIC_ARN no configurado"
**Solución**: Ejecuta `serverless deploy` para actualizar las variables de entorno.

### Error: "AccessDenied" al publicar en SNS
**Solución**: Agrega permisos `sns:Publish` al role IAM.

### No recibo emails pero los logs dicen "Email enviado exitosamente"
**Solución**: Verifica que la suscripción esté confirmada, no pendiente.

### Solo recibo emails para urgencia ALTA, no para MEDIA
**Solución**: Verifica que el código esté actualizado. Debería enviar para ambas.

