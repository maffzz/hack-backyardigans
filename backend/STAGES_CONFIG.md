## Uso de Diferentes Stages

El stage ahora es **completamente dinámico** usando `${sls:stage, 'dev'}` en `serverless.yml`, lo que significa que no hay hardcodeo y puedes pasar cualquier stage como parámetro.

### Desplegar a Dev (por defecto)

```bash
cd backend
serverless deploy
# o explícitamente:
serverless deploy --stage dev
```

### Desplegar a Staging

```bash
cd backend
serverless deploy --stage staging
```

Esto creará recursos con nombres como:
- Lambdas: `alertautec-backend-staging-*`
- Buckets: `alertautec-backend-attachments-staging`
- Tablas: `Incidentes` (mismo nombre, pero puedes usar prefijos si quieres)

### Desplegar a Producción

```bash
cd backend
serverless deploy --stage prod
```

### Desplegar a cualquier stage personalizado

```bash
cd backend
serverless deploy --stage mi-stage-personalizado
```

## Configuración por Stage

El `serverless.yml` usa la sintaxis moderna de Serverless Framework:

```yaml
provider:
  stage: ${sls:stage, 'dev'}  # Stage dinámico, 'dev' es el valor por defecto
  environment:
    STAGE: ${self:provider.stage}  # Se resuelve automáticamente al stage actual
    # ... otras variables
```

**Nota**: `${sls:stage}` es la sintaxis de Serverless Framework v3+. Si usas una versión anterior, puedes usar `${opt:stage, 'dev'}` que es compatible con versiones anteriores.APIs → websocket-backend-dev → Settings → WebSocket URL
```

**Configurar:**
```bash
# Opción 1: Variable de entorno antes del deploy
export WS_ENDPOINT="https://xxxxx.execute-api.us-east-1.amazonaws.com/dev"
cd backend
serverless deploy

# Opción 2: En serverless.yml (editar manualmente)
WS_ENDPOINT: "https://xxxxx.execute-api.us-east-1.amazonaws.com/dev"
```

### 2. `API_ENDPOINT` (Para seeders)

Endpoint del API Gateway HTTP. Se usa solo en scripts de seed.

**Obtener el endpoint:**
```bash
cd backend
serverless info

# O desde AWS Console:
# API Gateway → APIs → alertautec-backend-dev → Settings → Invoke URL
```

**Configurar para seeders:**
```bash
export API_ENDPOINT="https://xxxxx.execute-api.us-east-1.amazonaws.com/dev"
cd backend/seed
python seeder.py
```

## Uso de Diferentes Stages

El stage ahora es **completamente dinámico** usando `${sls:stage, 'dev'}` en `serverless.yml`, lo que significa que no hay hardcodeo y puedes pasar cualquier stage como parámetro.

### Desplegar a Dev (por defecto)

```bash
cd backend
serverless deploy
# o explícitamente:
serverless deploy --stage dev
```

### Desplegar a Staging

```bash
cd backend
serverless deploy --stage staging
```

Esto creará recursos con nombres como:
- Lambdas: `alertautec-backend-staging-*`
- Buckets: `alertautec-backend-attachments-staging`
- Tablas: `Incidentes` (mismo nombre, pero puedes usar prefijos si quieres)

### Desplegar a Producción

```bash
cd backend
serverless deploy --stage prod
```

### Desplegar a cualquier stage personalizado

```bash
cd backend
serverless deploy --stage mi-stage-personalizado
```

## Configuración por Stage

El `serverless.yml` usa la sintaxis moderna de Serverless Framework:

```yaml
provider:
  stage: ${sls:stage, 'dev'}  # Stage dinámico, 'dev' es el valor por defecto
  environment:
    STAGE: ${self:provider.stage}  # Se resuelve automáticamente al stage actual
    # ... otras variables
```

**Nota**: `${sls:stage}` es la sintaxis de Serverless Framework v3+. Si usas una versión anterior, puedes usar `${opt:stage, 'dev'}` que es compatible con versiones anteriores.

O crear archivos de configuración separados usando el plugin `serverless-stage-manager`:

```bash
npm install --save-dev serverless-stage-manager
```

## Ejemplo: Archivo .env (Opcional)

Puedes crear un archivo `.env` para desarrollo local (no se usa en Lambda, solo para scripts):

```bash
# .env
STAGE=dev
SERVICE_NAME=alertautec-backend
AWS_REGION=us-east-1
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
WS_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
```

Luego usar `python-dotenv` en scripts locales:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Verificación

Para verificar que las variables están configuradas correctamente:

```bash
# Ver variables de una Lambda específica
aws lambda get-function-configuration \
  --function-name alertautec-backend-dev-createIncident \
  --query 'Environment.Variables'
```

## Migración desde Hardcodeo

Todos los archivos han sido actualizados para usar variables de entorno:

✅ `common/authorize.py` - Usa `VALIDATE_TOKEN_LAMBDA`
✅ `staff/assignDepartment.py` - Usa `NOTIFY_DEPT_LAMBDA` y `REPORTS_BUCKET`
✅ `student/healthCheck.py` - Usa `WS_ENDPOINT`
✅ `seed/seeder.py` - Usa `API_ENDPOINT`
✅ `seed/seed_buckets.py` - Usa `SERVICE_NAME` y `STAGE`

## Notas Importantes

1. **Tablas DynamoDB**: Por defecto tienen el mismo nombre en todos los stages. Si quieres separarlos, agrega el stage al nombre en `serverless.yml`.

2. **IAM Role**: El role IAM (`LabRole`) debe tener permisos para todos los stages o crear roles separados.

3. **WebSocket**: El `websocket-backend` también debe desplegarse con el mismo stage para que coincidan los nombres.

4. **SNS Topics**: Se crean automáticamente con el stage en el nombre.

## Troubleshooting

**Problema**: Lambda no encuentra otra Lambda
**Solución**: Verifica que ambas estén desplegadas con el mismo stage y que `VALIDATE_TOKEN_LAMBDA` o `NOTIFY_DEPT_LAMBDA` estén correctamente configuradas.

**Problema**: WebSocket no funciona
**Solución**: Verifica que `WS_ENDPOINT` esté configurado correctamente en `serverless.yml` o como variable de entorno.

**Problema**: Seeder no encuentra el API
**Solución**: Configura `API_ENDPOINT` antes de ejecutar el seeder.

