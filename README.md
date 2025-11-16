
# AlertaUTEC – Plataforma de gestión de incidentes en campus

AlertaUTEC es una plataforma para **reportar, gestionar y monitorear incidentes** dentro del campus de UTEC.

Combina un backend **serverless en AWS** (Lambdas + DynamoDB + S3 + API Gateway REST/WebSocket) con un componente de **orquestación batch en Apache Airflow sobre ECS Fargate**, que genera reportes y dispara notificaciones automáticas a los departamentos.

Este README resume:

- Qué problema resuelve la app.
- Cómo está dividida en microservicios.
- Cómo funciona la capa de WebSockets en tiempo real.
- Cómo Airflow orquesta procesos sobre los datos de DynamoDB.

---

## 1. Problema que resolvemos

En el campus se producen incidentes de todo tipo (infraestructura, seguridad, etc.). Hoy se reportan de forma desordenada, sin trazabilidad ni notificaciones claras a los departamentos responsables.

**AlertaUTEC** permite:

- Que estudiantes reporten incidentes desde un frontend simple (web).
- Adjuntar evidencia (fotos, archivos) a cada incidente.
- Que staff/admin gestione el ciclo de vida del incidente (asignar departamento, cambiar estado, comentar).
- Ver estadísticas básicas y reportes agregados.
- Disparar notificaciones en tiempo real vía WebSockets.
- Orquestar procesos batch de análisis y notificación usando Airflow.

---

## 2. Arquitectura general

La solución está dividida en varios componentes:

- **Backend REST (Serverless Framework)** – `backend/serverless.yml`
  - Autenticación (`auth/*`).
  - Funciones para estudiantes (`student/*`).
  - Funciones para staff/admin (`staff/*`).
  - Tablas DynamoDB y buckets S3.

- **Backend WebSocket** – `backend/websocket-backend/*`
  - API Gateway WebSocket + Lambdas para manejo de conexiones y broadcast de eventos.

- **Airflow en ECS Fargate** (repo separado `airflow-alertautec`)
  - Imagen Docker basada en `apache/airflow:2.9.0` con `boto3` y el DAG `alerta_utec_orchestracion.py` embebido.
  - Corre en Fargate usando `LabRole` para hablar con DynamoDB, S3 y Lambda.

- **Frontend (no incluido aquí)**
  - Consume las APIs REST.
  - Se conecta al WebSocket para recibir notificaciones en tiempo real.

### 2.1. Recursos principales en AWS

- **DynamoDB**
  - `Users` – usuarios de la plataforma.
  - `Tokens` – tokens de sesión.
  - `Incidentes` – incidentes reportados (`incident_id`, `tipo`, `descripcion`, `ubicacion`, `urgencia`, `estado`, `departamento`, timestamps, etc.).
  - `IncidenteEventos` – historial de eventos por incidente (cambios de estado, comentarios, asignaciones de departamento).
  - `Departamentos` – catálogo de departamentos (futuro punto para emails/contactos).
  - `websocket-backend-*-connections` – conexiones activas para WebSockets.

- **S3**
  - `alertautec-backend-attachments-dev` – adjuntos de incidentes (fotos, archivos).
  - `alertautec-backend-reportes-dev` – reportes generados por Airflow (globales e individuales por incidente/departamento).

- **Lambda** (algunos ejemplos)
  - `RegisterUser`, `GenerateToken`, `ValidarTokenAcceso`.
  - `createIncident`, `listIncidents`, `listMine`, `getIncident`, `uploadAttachment`, `statsBasic`.
  - `updateStatus`, `addComment`, `assignDepartment`, `listForDepartment`, `getIncidentEvents`, `staffStats`.
  - `notifyDepartmentIncident` – invocada por Airflow para procesar una notificación de incidente hacia un departamento (por ahora registra logs y valida S3, lista para integrar SES/SNS).

- **API Gateway REST**
  - Rutas `student/*` y `staff/*` para el frontend.

- **API Gateway WebSocket**
  - Canal de comunicación en tiempo real para notificaciones.

---

## 3. Microservicios / módulos del backend

### 3.1. Autenticación – `backend/auth/*`

- **`RegisterUser`**
  - Registro de nuevos usuarios en la tabla `Users`.

- **`GenerateToken`**
  - Login: genera un token de acceso y lo guarda en `Tokens`.

- **`ValidarTokenAcceso`**
  - Endpoint interno usado por `common/authorize.py`.
  - Valida el token que viene en los headers de cada petición.

### 3.2. Student – `backend/student/*`

- **`createIncident`**
  - Recibe los datos del incidente desde el frontend.
  - Valida y guarda un item nuevo en `Incidentes`.
  - Dispara una notificación WebSocket (`notify_incident_created`).

- **`listIncidents` / `listMine` / `getIncident`**
  - Listados y detalle de incidentes, filtrados por usuario o global.

- **`uploadAttachment`**
  - Usa el bucket `S3_BUCKET` (`alertautec-backend-attachments-dev`).
  - Guarda archivos asociados a un `incident_id`.

- **`validateLocation` / `previewIncident` / `statsBasic`**
  - Validaciones y estadísticas básicas de uso (recuentos por estado, etc.).

### 3.3. Staff / Admin – `backend/staff/*`

- **`updateStatus`**
  - Cambia el estado de un incidente (p. ej. `pendiente → en_proceso → resuelto`).
  - Registra un evento en `IncidenteEventos`.
  - Notifica por WebSocket (`notify_incident_status_changed`).

- **`addComment`**
  - Permite agregar comentarios internos al incidente.
  - Registra evento en `IncidenteEventos` y notifica por WebSocket.

- **`assignDepartment`**
  - Sólo para usuarios con rol `admin`.
  - Actualiza el campo `departamento` en `Incidentes`.
  - Registra un evento de tipo `asignacion` en `IncidenteEventos` con `detalle.departamento`.
  - Notifica por WebSocket (`notify_department_assigned`).

- **`listForDepartment`**
  - Lista incidentes filtrados por departamento asignado.

- **`getIncidentEvents` / `staffStats`**
  - Historial de eventos por incidente y estadísticas para staff.

- **`notifyDepartmentIncident`** (nuevo)
  - Lambda pensada para ser invocada desde Airflow.
  - Input: `incident_id`, `departamento`, `s3_bucket`, `s3_key`.
  - Lee el incidente en `Incidentes`.
  - Verifica que el objeto S3 con el reporte exista.
  - Registra en logs la “notificación” hacia el departamento.
  - Lista para integrar SES / SNS en el futuro.

### 3.4. WebSocket backend – `backend/websocket-backend/*`

- **Conexiones (`handlers/connect.py`, `disconnect.py`)**
  - Guarda y elimina `connectionId` en la tabla `WebSocketConnections`.

- **Notificaciones (`common/notifications.py`)**
  - Funciones de broadcast usando el API Gateway Management API.
  - Notificaciones específicas:
    - `notifyIncidentCreated`.
    - `notifyIncidentStatusChanged`.
    - `notifyCommentAdded`.
    - `notifyDepartmentAssigned`.

- **Invocación desde backend principal – `backend/common/websocket.py`**
  - Lambdas del backend principal invocan a las Lambdas del websocket-backend asíncronamente usando `boto3`.
  - Resultado: los clientes conectados al WebSocket reciben eventos en tiempo real.

---

## 4. Orquestación con Airflow en ECS Fargate

Para la capa de orquestación batch se despliega un **Apache Airflow 2.9.0** en **ECS Fargate**:

- Imagen Docker (`airflow-alertautec/Dockerfile`):
  - Base: `apache/airflow:2.9.0-python3.10`.
  - Instala `boto3`.
  - Copia el DAG al contenedor: `COPY dags/ /opt/airflow/dags/`.

- Despliegue en ECS Fargate:
  - Task Definition con contenedor `airflow`.
  - `Task role` = `LabRole` (permite acceso a DynamoDB, S3 y Lambda).
  - Comando de inicio: `airflow standalone` (inicializa DB local SQLite, webserver y scheduler en un solo contenedor).
  - Exposición de puerto `8080` para la UI de Airflow.

- Configuración principal (variables de entorno de la Task):
  - `AIRFLOW__CORE__EXECUTOR=SequentialExecutor` (sin RDS, usando SQLite local).
  - `AWS_REGION=us-east-1`.
  - `REPORTS_BUCKET=alertautec-backend-reportes-dev`.
  - `NOTIFY_DEPT_LAMBDA=alertautec-backend-dev-notifyDepartmentIncident`.

### 4.1. DAG `alertautec_orchestracion`

El DAG principal hace dos cosas:

1. **`generar_reporte_global`**
   - Lee todos los incidentes en `Incidentes`.
   - Calcula estadísticas agregadas:
     - Cantidad por `estado`, `tipo`, `urgencia`.
   - Escribe un JSON en `REPORTS_BUCKET`:
     - Ruta: `reportes/global/reporte_YYYY-MM-DD_HH-MM.json`.

2. **`procesar_asignaciones_departamentos`**
   - Lee la tabla `IncidenteEventos` filtrando `tipo_evento = "asignacion"` en una ventana de tiempo (ej. últimas 2 horas).
   - Por cada asignación:
     - Carga el incidente desde `Incidentes`.
     - Genera un reporte individual en S3:
       - `reportes/incidentes/{departamento}/incidente_{incident_id}.json`.
     - Invoca la Lambda `notifyDepartmentIncident` con:
       - `incident_id`, `departamento`, `s3_bucket`, `s3_key`.

De esta forma, Airflow se convierte en el **cerebro batch** que analiza los incidentes, genera reportes y dispara notificaciones hacia los departamentos usando la infraestructura serverless ya existente.

---

## 5. Flujo de datos resumido

1. **Estudiante crea incidente**
   - Frontend → API Gateway REST → Lambda `createIncident`.
   - Se guarda en `Incidentes`.
   - Se lanza `notifyIncidentCreated` vía WebSocket.

2. **Staff asigna departamento**
   - Frontend → `assignDepartment`.
   - Se actualiza `Incidentes.departamento` y se inserta evento `asignacion` en `IncidenteEventos`.
   - Se notifica al WebSocket (`notify_department_assigned`).

3. **Airflow detecta asignaciones y genera reportes**
   - El DAG `alertautec_orchestracion` escanea `IncidenteEventos`.
   - Genera reportes globales e individuales en S3 (`alertautec-backend-reportes-dev`).
   - Invoca `notifyDepartmentIncident` para cada nuevo incidente asignado.

4. **(Futuro) Notificación por correo**
   - La Lambda `notifyDepartmentIncident` está preparada para que, en una etapa siguiente, se integre con **SES/SNS** para enviar emails o mensajes directos a los departamentos.

---

## 6. Cómo correr el backend (resumen)

> Nota: este repo asume que ya tienes **Serverless Framework** configurado y credenciales de AWS válidas.

1. Instalar dependencias (si aplica):

   ```bash
   cd backend
   # pip install -r requirements.txt  # si se define
   ```

2. Desplegar backend serverless:

   ```bash
   cd backend
   sls deploy
   ```

   Esto crea:
   - Lambdas de `auth`, `student`, `staff`.
   - Tablas DynamoDB y buckets S3.
   - API Gateway REST.
   - Backend WebSocket.

3. Desplegar Airflow en ECS Fargate:

   - Usar el repo `airflow-alertautec` para build/push de la imagen.
   - Seguir la guía en `backend/README_airflow_ecs.md` para:
     - Crear la Task Definition.
     - Crear el Service en ECS Fargate.
     - Configurar env vars y roles (usando `LabRole`).

---

## 7. Puntos importantes

- **Arquitectura serverless completa**:
  - Backend en Lambdas + DynamoDB + S3.
  - WebSockets para notificaciones en tiempo real de cambios de estado y asignaciones.

- **Orquestación inteligente con Airflow en ECS Fargate**:
  - DAG que analiza incidentes, genera reportes y dispara notificaciones a departamentos.
  - Integrado con DynamoDB, S3 y Lambda.

- **Escalabilidad y mantenibilidad**:
  - Microservicios claros (`auth`, `student`, `staff`, `websocket-backend`).
  - Orquestación desacoplada en Airflow, que se puede extender con nuevas tareas (correos, ML, etc.).

AlertaUTEC no solo resuelve el problema de reportar incidentes, sino que también **estructura el flujo de comunicación y análisis**, dejando lista una base sólida para seguir creciendo en producción.
