
# 🚨 AlertaUTEC – Plataforma de gestión de incidentes en campus

AlertaUTEC es una plataforma para **reportar, gestionar y monitorear incidentes** dentro del campus de UTEC.

Combina un backend **serverless en AWS** (Lambdas + DynamoDB + S3 + API Gateway REST/WebSocket) con un componente de **orquestación batch en Apache Airflow** (corriendo en EC2 con Docker Compose, y desplegable en ECS Fargate), que genera reportes y dispara notificaciones automáticas a los departamentos. Además, se integra con **Amazon SageMaker** para análisis predictivo y modelos de ML entrenados sobre los incidentes históricos.

Este README resume:

- Qué problema resuelve la app.
- Cómo está dividida en microservicios.
- Cómo funciona la capa de WebSockets en tiempo real.
- Cómo Airflow orquesta procesos sobre los datos de DynamoDB y genera reportes en S3.
- Cómo SageMaker analiza los incidentes y expone un endpoint de predicción.
- Cómo probar todo con la colección de Postman incluida en el repo.

---

## 1. 🎯 Problema que resolvemos

En el campus se producen incidentes de todo tipo (infraestructura, seguridad, etc.). Hoy se reportan de forma desordenada, sin trazabilidad ni notificaciones claras a los departamentos responsables.

**AlertaUTEC** permite:

- Que estudiantes reporten incidentes desde un frontend simple (web).
- Adjuntar evidencia (fotos, archivos) a cada incidente.
- Que staff/admin gestione el ciclo de vida del incidente (asignar departamento, cambiar estado, comentar).
- Ver estadísticas básicas y reportes agregados.
- Disparar notificaciones en tiempo real vía WebSockets.
- Orquestar procesos batch de análisis y notificación usando Airflow.

---

## 2. 🧱 Arquitectura general

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

### 2.1. ☁️ Recursos principales en AWS

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

## 3. 🧩 Microservicios / módulos del backend

### 3.1. 🔐 Autenticación – `backend/auth/*`

- **`RegisterUser`**
  - Registro de nuevos usuarios en la tabla `Users`.

- **`GenerateToken`**
  - Login: genera un token de acceso y lo guarda en `Tokens`.

- **`ValidarTokenAcceso`**
  - Endpoint interno usado por `common/authorize.py`.
  - Valida el token que viene en los headers de cada petición.

### 3.2. 🎓 Student – `backend/student/*`

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

### 3.3. 🛠️ Staff / Admin – `backend/staff/*`

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
  - **Genera un reporte individual** del incidente asignado en S3.
  - **Invoca la Lambda `notifyDepartmentIncident`** inmediatamente para notificar al departamento.

- **`listByDepartment`**
  - Lista incidentes filtrados por departamento asignado (usado por el panel de staff).

-- **`getIncidentEvents` / `staffStats`**
  - Historial de eventos por incidente y estadísticas para staff.

- **`notifyDepartmentIncident`** (mejorada)
  - Lambda pensada para ser invocada desde Airflow **y** desde el backend cuando se asigna un departamento.
  - Input: `incident_id`, `departamento`, `s3_bucket`, `s3_key`.
  - Lee el incidente en `Incidentes` y valida que el reporte exista en S3.
  - Publica un mensaje en **SNS** usando el topic `IncidentNotificationsTopic` (configurado en `serverless.yml`).
  - Envía un correo a los responsables del departamento (vía SNS), incluyendo resumen del incidente y link directo al reporte en S3.
  - Loggea el resultado (incluyendo si el email fue enviado correctamente).

- **`notifyUrgentIncident`** (nuevo)
  - Lambda para incidentes **EMERGENCIA / ALTA**.
  - Se invoca desde `student/createIncident` cuando el tipo/urgencia lo requiere.
  - Publica en SNS una alerta prioritaria, reutilizando la misma infraestructura de notificaciones.

### 3.4. 🔌 WebSocket backend – `backend/websocket-backend/*`

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

## 4. 🌀 Orquestación con Airflow (EC2 Docker Compose / ECS)

Para la capa de orquestación batch se usa **Apache Airflow 2.10.x**:

- **Desarrollo / demo:**
  - Airflow corre en una instancia **EC2** usando `docker-compose` (ver carpeta `airflow-alertautec/airflow`).
  - Servicios: `airflow-webserver`, `airflow-scheduler`, `airflow-worker`, `redis`, `postgres`.
  - Se monta `~/.aws` dentro de los contenedores para que `boto3` pueda usar las credenciales de AWS y hablar con DynamoDB, S3 y Lambda.

- **Producción (conceptual):**
  - La misma imagen Docker puede desplegarse en **ECS Fargate**, con una Task Definition y Services separados para webserver/scheduler.
  - `Task role` = `LabRole` (permite acceso a DynamoDB, S3 y Lambda).

- Configuración principal (env vars):
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
   - Se genera un reporte individual en S3 y se invoca `notifyDepartmentIncident` para notificar por correo al departamento.

3. **Airflow detecta asignaciones y genera reportes**
   - El DAG `alertautec_orchestracion` escanea `IncidenteEventos`.
   - Genera reportes globales e individuales en S3 (`alertautec-backend-reportes-dev`).
   - Invoca `notifyDepartmentIncident` para cada nuevo incidente asignado (modo batch).

4. **Notificación por correo**
   - La Lambda `notifyDepartmentIncident` ya está integrada con **SNS** y envía emails a los responsables de cada departamento, incluyendo link al reporte en S3.

---

## 6. 🏃‍♀️ Cómo correr el backend (resumen)

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

## 7. ✨ Puntos importantes

- **Arquitectura serverless completa**:
  - Backend en Lambdas + DynamoDB + S3.
  - WebSockets para notificaciones en tiempo real de cambios de estado y asignaciones.

- **Orquestación inteligente con Airflow**:
  - DAG que analiza incidentes, genera reportes y dispara notificaciones a departamentos.
  - Integrado con DynamoDB, S3 y Lambda, corriendo en EC2 con Docker Compose (y listo para ECS).

- **Escalabilidad y mantenibilidad**:
  - Microservicios claros (`auth`, `student`, `staff`, `websocket-backend`).
  - Orquestación desacoplada en Airflow, que se puede extender con nuevas tareas (correos, ML, etc.).

- **Análisis predictivo y ML con SageMaker**:
  - Notebook en SageMaker AI que consume los incidentes desde DynamoDB.
  - Análisis de patrones (zonas de riesgo, horas pico, tipos frecuentes).
  - Modelo de clasificación (RandomForest / XGBoost) para predecir el tipo de incidente más probable según zona, hora y urgencia.
  - Integración con un endpoint de SageMaker a través de la Lambda `staff/predictRisk`, accesible solo para `staff` y `admin`.

- **Notificaciones avanzadas**:
  - WebSocket para tiempo real (creación, cambios de estado, comentarios, asignaciones).
  - SNS + email para notificar a departamentos sobre nuevos incidentes asignados y emergencias.

- **Experiencia de pruebas amigable**:
  - Colección Postman en `backend/Postman_Collection.json` con variables (`baseUrl`, `token_student`, `token_staff`, `token_admin`, `incident_id`).
  - Carpetas organizadas por rol (Auth, Student, Staff/Admin, ML & Notificaciones) para probar todos los flujos end-to-end.

AlertaUTEC no solo resuelve el problema de reportar incidentes, sino que también **estructura el flujo de comunicación, análisis y predicción**, dejando lista una base sólida para seguir creciendo en producción 🚀.
