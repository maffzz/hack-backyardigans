import json
import os
from collections import Counter

import boto3

# Configuración básica
REGION = os.environ.get("AWS_REGION", "us-east-1")

# Deben coincidir con los nombres definidos en serverless.yml
#   AttachmentsBucket: ${self:service}-attachments-${self:provider.stage}
#   ReportsBucket:     ${self:service}-reportes-${self:provider.stage}
ATTACHMENTS_BUCKET = os.environ.get("ATTACHMENTS_BUCKET", "alertautec-backend-attachments-dev")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", "alertautec-backend-reportes-dev")

s3 = boto3.client("s3", region_name=REGION)


def load_incidents(seed_path: str = "seed_incidents.json"):
    if not os.path.exists(seed_path):
        print(f"[WARN] No existe {seed_path}, no se generarán seeds para buckets")
        return []
    with open(seed_path) as f:
        return json.load(f)


def seed_attachments(incidents):
    """Sube archivos de ejemplo al bucket de adjuntos.

    Crea, para cada incidente, un archivo de texto simple que simula ser
    una evidencia subida por el estudiante.
    """
    if not incidents:
        return

    print(f"[INFO] Sembrando adjuntos en bucket: {ATTACHMENTS_BUCKET}")

    for inc in incidents:
        incident_id = inc.get("incident_id") or inc.get("id")
        if not incident_id:
            continue

        key = f"{incident_id}/seed_evidencia.txt"
        body = (
            f"Incidente {incident_id}\n"
            f"Tipo: {inc.get('tipo', 'N/A')}\n"
            f"Urgencia: {inc.get('urgencia', 'N/A')}\n"
            f"Descripción: {inc.get('descripcion', '')[:200]}\n"
        )
        try:
            s3.put_object(Bucket=ATTACHMENTS_BUCKET, Key=key, Body=body.encode("utf-8"))
            print(f"[OK] Adjuntar dummy -> s3://{ATTACHMENTS_BUCKET}/{key}")
        except Exception as e:
            print(f"[ERROR] Subiendo adjunto para {incident_id}: {e}")


def seed_reports(incidents):
    """Crea reportes de ejemplo en el bucket de reportes.

    - Un reporte global con estadísticas agregadas.
    - Un reporte individual por incidente agrupado por departamento.
    """
    if not incidents:
        return

    print(f"[INFO] Sembrando reportes en bucket: {REPORTS_BUCKET}")

    # Reporte global simple
    estados = Counter(inc.get("estado", "desconocido") for inc in incidents)
    tipos = Counter(inc.get("tipo", "desconocido") for inc in incidents)
    urgencias = Counter(inc.get("urgencia", "desconocida") for inc in incidents)

    global_report = {
        "total_incidentes": len(incidents),
        "por_estado": dict(estados),
        "por_tipo": dict(tipos),
        "por_urgencia": dict(urgencias),
    }

    try:
        s3.put_object(
            Bucket=REPORTS_BUCKET,
            Key="reportes/global/seed_reporte_global.json",
            Body=json.dumps(global_report, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        print("[OK] Reporte global -> s3://" + REPORTS_BUCKET + "/reportes/global/seed_reporte_global.json")
    except Exception as e:
        print(f"[ERROR] Subiendo reporte global: {e}")

    # Reportes individuales por incidente/departamento
    for inc in incidents:
        incident_id = inc.get("incident_id") or inc.get("id")
        if not incident_id:
            continue

        departamento = inc.get("departamento", "sin_departamento")
        key = f"reportes/incidentes/{departamento}/incidente_{incident_id}.json"

        reporte_incidente = {
            "incident_id": incident_id,
            "departamento": departamento,
            "tipo": inc.get("tipo"),
            "estado": inc.get("estado"),
            "urgencia": inc.get("urgencia"),
            "descripcion": inc.get("descripcion"),
        }

        try:
            s3.put_object(
                Bucket=REPORTS_BUCKET,
                Key=key,
                Body=json.dumps(reporte_incidente, indent=2).encode("utf-8"),
                ContentType="application/json",
            )
            print(f"[OK] Reporte incidente -> s3://{REPORTS_BUCKET}/{key}")
        except Exception as e:
            print(f"[ERROR] Subiendo reporte de incidente {incident_id}: {e}")


def main():
    incidents = load_incidents()
    seed_attachments(incidents)
    seed_reports(incidents)


if __name__ == "__main__":
    main()
