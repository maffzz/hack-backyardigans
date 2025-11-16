# Guía: Airflow en ECS Fargate integrado con alertautec-backend

Este documento explica paso a paso cómo desplegar **Apache Airflow en ECS Fargate** y conectarlo con el backend serverless `alertautec-backend` para:

- Leer incidentes desde DynamoDB (`Incidentes`).
- Generar reportes agregados en S3 (`REPORTS_BUCKET`).
- Procesar asignaciones de incidentes a departamentos (`IncidenteEventos`).
- Invocar la Lambda `notifyDepartmentIncident` para notificar a departamentos.

> Pensado para la hackathon: enfoque práctico, arquitectura limpia y fácil de explicar en la demo.

---

## 0. Prerrequisitos

- Cuenta AWS con permisos para:
  - ECR, ECS, IAM, RDS, S3, Lambda, DynamoDB.
- Backend `alertautec-backend` desplegado con `serverless.yml` actualizado:
  - Tablas DynamoDB: `Incidentes`, `IncidenteEventos`, `Departamentos`.
  - Lambdas de negocio (`createIncident`, `assignDepartment`, etc.).
  - **Lambda nueva**: `notifyDepartmentIncident`:
    - Archivo: `backend/staff/notifyDepartmentIncident.py`.
    - Registrada en `serverless.yml` como:

      ```yaml
      notifyDepartmentIncident:
        handler: staff/notifyDepartmentIncident.handler
      ```

  - Buckets S3 gestionados por Serverless:
    - Adjuntos: `${self:service}-attachments-${self:provider.stage}`
    - Reportes: `${self:service}-reportes-${self:provider.stage}`
  - Variables de entorno en `serverless.yml`:

    ```yaml
    provider:
      environment:
        STAGE: ${self:provider.stage}
        S3_BUCKET: ${self:service}-attachments-${self:provider.stage}
        REPORTS_BUCKET: ${self:service}-reportes-${self:provider.stage}
    ```

- `serverless deploy` ejecutado en `backend/` para crear todas las Lambdas y buckets.

---

## 1. Imagen Docker de Airflow y ECR

### 1.1. Crear repositorio ECR

En tu terminal:

```bash
aws ecr create-repository --repository-name airflow-utec
```

Anota:

- `ACCOUNT_ID`: ID de tu cuenta.
- `REGION`: normalmente `us-east-1`.

### 1.2. Crear Dockerfile de Airflow

En un repo separado (o carpeta `airflow/`), crea un `Dockerfile`:

```dockerfile
FROM apache/airflow:2.9.0-python3.10

# Instalar dependencias necesarias para interactuar con AWS
RUN pip install boto3

# Opcional: copiar directamente el DAG dentro de la imagen
# COPY dags/ /opt/airflow/dags/
```

- Si copias el DAG dentro de la imagen, asegúrate de tener una carpeta `dags/` con `alertautec_orchestracion.py`.

### 1.3. Build y push de la imagen a ECR

```bash
ACCOUNT_ID=<tu_account_id>
REGION=us-east-1

# Build imagen
docker build -t airflow-utec .

# Tag para ECR
docker tag airflow-utec:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/airflow-utec:latest

# Login a ECR
aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Push
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/airflow-utec:latest
```

---

## 2. Base de Datos RDS para Airflow

Airflow necesita una base de datos para metadatos (DAGs, logs, estados).

### 2.1. Crear PostgreSQL en RDS

En consola AWS:

1. Ir a **RDS → Create database**.
2. Engine: **PostgreSQL** (versión estable, p.ej. 14.x).
3. Template: `Free tier` si aplica.
4. Credenciales:
   - DB name: `airflow`
   - Master username: `airflow`
   - Master password: `airflow_pass` (elige una segura).
5. TIPO instancia pequeña (p.ej. `db.t3.micro`).
6. Asegúrate que la VPC/Subnets coincidan con las que usarás en ECS.

Al final tendrás un endpoint tipo:

```text
<rds-endpoint>.rds.amazonaws.com:5432
```

Cadena de conexión para Airflow (`SQL_ALCHEMY_CONN`):

```text
postgresql+psycopg2://airflow:airflow_pass@<rds-endpoint>:5432/airflow
```

> Ajusta usuario/contraseña según lo que hayas configurado.

---

## 3. Buckets S3 para logs y DAGs (opcional)

### 3.1. Bucket para logs de Airflow

Crear un bucket para logs, por ejemplo:

```bash
aws s3 mb s3://airflow-logs-utec
```

Variables de entorno en la tarea ECS:

```text
AIRFLOW__LOGGING__REMOTE_LOGGING=True
AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=s3://airflow-logs-utec/logs
```

### 3.2. Bucket para DAGs (opcional)

Para la hackathon es totalmente válido **no usar** bucket de DAGs y meter el DAG en la imagen.

Si quisieras usar S3 para DAGs, necesitarías lógica adicional en el contenedor para descargar los DAGs al iniciar (fuera de alcance de esta guía básica).

---

## 4. Cluster ECS Fargate

1. Ir a **ECS → Clusters → Create Cluster**.
2. Tipo: `Networking only (Fargate)`.
3. Nombre: `airflow-cluster` (por ejemplo).
4. Selecciona la VPC y subnets donde está tu RDS (o donde tendrá acceso a él).

---

## 5. Task Definition de ECS para Airflow

### 5.1. Crear Task Definition (Fargate)

En ECS → Task Definitions → `Create new Task Definition`:

- Launch type: **Fargate**.
- Task memory: `1 GB` o `2 GB`.
- Task CPU: `0.5 vCPU (512)` o `1 vCPU (1024)`.

### 5.2. Definir el contenedor de Airflow

- Container name: `airflow`.
- Image:

  ```text
  $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/airflow-utec:latest
  ```

- Port mappings:
  - Container port: `8080` (Airflow webserver).

- Command (override):

  ```bash
  bash -c "airflow db upgrade && airflow webserver & airflow scheduler"
  ```

  Esto:
  - Ejecuta migraciones de DB (`db upgrade`).
  - Inicia `webserver` (en background).
  - Inicia `scheduler` en el mismo contenedor.

### 5.3. Variables de entorno del contenedor

En la sección de **Environment variables**, agrega:

```text
# Ejecutores y DB
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow_pass@<rds-endpoint>:5432/airflow

# Región AWS
AWS_REGION=us-east-1

# Integración con alertautec-backend
REPORTS_BUCKET=alertautec-backend-reportes-dev
NOTIFY_DEPT_LAMBDA=alertautec-backend-dev-notifyDepartmentIncident

# Logs (si usas S3 para logs)
AIRFLOW__LOGGING__REMOTE_LOGGING=True
AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=s3://airflow-logs-utec/logs
```

> Cambia `<rds-endpoint>` por el endpoint real de tu DB RDS.

### 5.4. Roles IAM de la tarea

**Task Execution Role**: rol estándar de ECS para:

- Pull de ECR.
- Logs en CloudWatch.

**Task Role** (muy importante):

Debe permitir a Airflow:

- DynamoDB:
  - `dynamodb:Scan` y `dynamodb:GetItem` en tablas:
    - `Incidentes`
    - `IncidenteEventos`
- S3:
  - `s3:PutObject` en `alertautec-backend-reportes-dev/*`.
  - `s3:PutObject`, `s3:GetObject` en `airflow-logs-utec/*` (si usas logs en S3).
- Lambda:
  - `lambda:InvokeFunction` en `alertautec-backend-dev-notifyDepartmentIncident`.

Ejemplo de política (alto nivel, NO es JSON completo, solo referencia):

```text
Effect: Allow
Action:
  - dynamodb:Scan
  - dynamodb:GetItem
Resource: arn:aws:dynamodb:us-east-1:<account_id>:table/Incidentes

Effect: Allow
Action:
  - dynamodb:Scan
  - dynamodb:GetItem
Resource: arn:aws:dynamodb:us-east-1:<account_id>:table/IncidenteEventos

Effect: Allow
Action:
  - s3:PutObject
Resource: arn:aws:s3:::alertautec-backend-reportes-dev/*

Effect: Allow
Action:
  - s3:PutObject
  - s3:GetObject
Resource: arn:aws:s3:::airflow-logs-utec/*

Effect: Allow
Action:
  - lambda:InvokeFunction
Resource: arn:aws:lambda:us-east-1:<account_id>:function:alertautec-backend-dev-notifyDepartmentIncident
```

Adjunta esta política al **Task Role** de ECS.

---

## 6. Servicio ECS (Airflow corriendo en Fargate)

1. En ECS → Clusters → selecciona `airflow-cluster`.
2. Crea un **Service**:
   - Launch type: Fargate.
   - Task definition: la que creaste para Airflow.
   - Desired tasks: `1`.
   - Network:
     - VPC: misma de RDS.
     - Subnets: públicas o privadas con acceso a RDS.
     - Security group: debe permitir:
       - Salida hacia RDS (puerto 5432).
       - Entrada HTTP al puerto 8080 (si expones la UI vía Load Balancer o SG abierto).

3. Opcional: configurar un **Application Load Balancer** para acceder al webserver:
   - Target group apuntando al puerto 8080 de la tarea.
   - Listener HTTP 80 o HTTPS 443.

Cuando el servicio esté en estado `Running`, Airflow:

- Conectará a RDS y hará `db upgrade`.
- Iniciará `webserver` y `scheduler`.
- Detectará los DAGs que tenga en `/opt/airflow/dags/`.

---

## 7. DAG `alertautec_orchestracion`

Crea un archivo Python con el DAG en el entorno de Airflow (si los empacas en la imagen, ponlo dentro de `dags/` antes de hacer `docker build`).

Nombre: `alertautec_orchestracion.py`

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import boto3
import json
import os

REGION = "us-east-1"
INCIDENTS_TABLE = "Incidentes"
EVENTS_TABLE = "IncidenteEventos"

# Debe coincidir con REPORTS_BUCKET del backend
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", "alertautec-backend-reportes-dev")

# Nombre completo de la lambda en AWS (ajusta stage si cambia)
LAMBDA_NOTIFY = os.environ.get(
    "NOTIFY_DEPT_LAMBDA",
    "alertautec-backend-dev-notifyDepartmentIncident"
)

dynamo = boto3.resource("dynamodb", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)


def generar_reporte_global():
    table = dynamo.Table(INCIDENTS_TABLE)
    items = table.scan().get("Items", [])

    stats = {
        "total": len(items),
        "por_estado": {},
        "por_tipo": {},
        "por_urgencia": {},
    }

    for inc in items:
        estado = inc.get("estado", "desconocido")
        tipo = inc.get("tipo", "desconocido")
        urgencia = inc.get("urgencia", "desconocida")

        stats["por_estado"][estado] = stats["por_estado"].get(estado, 0) + 1
        stats["por_tipo"][tipo] = stats["por_tipo"].get(tipo, 0) + 1
        stats["por_urgencia"][urgencia] = stats["por_urgencia"].get(urgencia, 0) + 1

    key = f"reportes/global/reporte_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M')}.json"
    s3.put_object(
        Bucket=REPORTS_BUCKET,
        Key=key,
        Body=json.dumps({
            "stats": stats,
            "generated_at": datetime.utcnow().isoformat(),
        }),
    )


def procesar_asignaciones_departamentos():
    table_evt = dynamo.Table(EVENTS_TABLE)
    table_inc = dynamo.Table(INCIDENTS_TABLE)

    # Ventana simple: últimas 2 horas
    desde = datetime.utcnow() - timedelta(hours=2)

    eventos = table_evt.scan().get("Items", [])
    for evt in eventos:
        if evt.get("tipo_evento") != "asignacion":
            continue

        ts = evt.get("timestamp")
        try:
            ts_dt = datetime.fromisoformat(ts)
        except Exception:
            continue

        if ts_dt < desde:
            continue

        incident_id = evt.get("incident_id")
        detalle = evt.get("detalle", {})
        departamento = detalle.get("departamento")

        if not incident_id or not departamento:
            continue

        # Obtener incidente completo
        inc_resp = table_inc.get_item(Key={"incident_id": incident_id})
        incident = inc_resp.get("Item")
        if not incident:
            continue

        # Crear reporte individual en S3
        key = f"reportes/incidentes/{departamento}/incidente_{incident_id}.json"
        reporte = {
            "incident": incident,
            "asignacion_event": evt,
            "generated_at": datetime.utcnow().isoformat(),
        }
        s3.put_object(
            Bucket=REPORTS_BUCKET,
            Key=key,
            Body=json.dumps(reporte),
        )

        # Invocar Lambda notifyDepartmentIncident (asíncrona)
        payload = {
            "incident_id": incident_id,
            "departamento": departamento,
            "s3_bucket": REPORTS_BUCKET,
            "s3_key": key,
        }
        lambda_client.invoke(
            FunctionName=LAMBDA_NOTIFY,
            InvocationType="Event",
            Payload=json.dumps(payload),
        )


with DAG(
    dag_id="alertautec_orchestracion",
    description="Orquestación de reportes y notificaciones por departamentos para AlertaUTEC",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/30 * * * *",  # cada 30 minutos
    catchup=False,
) as dag:

    generar_reporte_global_task = PythonOperator(
        task_id="generar_reporte_global",
        python_callable=generar_reporte_global,
    )

    procesar_asignaciones_task = PythonOperator(
        task_id="procesar_asignaciones_departamentos",
        python_callable=procesar_asignaciones_departamentos,
    )

    generar_reporte_global_task >> procesar_asignaciones_task
```

---

## 8. Checklist rápida para ti

1. `serverless deploy` en `backend/` (ya hecho o por hacer) para crear:
   - Lambda `notifyDepartmentIncident`.
   - Buckets de adjuntos y reportes.
2. Crear imagen de Airflow y subir a ECR.
3. Crear RDS PostgreSQL para Airflow.
4. Crear bucket `airflow-logs-utec` (si quieres logs remotos).
5. Crear cluster ECS Fargate.
6. Crear Task Definition con:
   - Imagen de Airflow.
   - Variables de entorno (`SQL_ALCHEMY_CONN`, `REPORTS_BUCKET`, `NOTIFY_DEPT_LAMBDA`, etc.).
   - Task Role con permisos de DynamoDB, S3 y Lambda.
7. Crear Service de ECS con 1 tarea.
8. Asegurar conectividad ECS ↔ RDS ↔ S3 ↔ Lambda.
9. Ver en la UI de Airflow que aparece el DAG `alertautec_orchestracion` y activarlo.

Con esto tienes una historia redonda para la hackathon: **Airflow en ECS Fargate orquesta procesos batch sobre el backend serverless y potencia AlertaUTEC con reportes y notificaciones automáticas.**
