import json
import requests

API = "https://4f7f6il2j5.execute-api.us-east-1.amazonaws.com/dev"

# Usuarios
with open("seed_users.json") as f:
    users = json.load(f)
for u in users:
    r = requests.post(f"{API}/auth/register", json=u)
    print("USER", u["user_id"], r.status_code, r.text)

# Incidentes
with open("seed_incidents.json") as f:
    incidents = json.load(f)
for inc in incidents:
    payload = inc.copy()
    if isinstance(payload.get('ubicacion'), dict):
        for k, v in payload['ubicacion'].items():
            payload[f"ubicacion_{k}"] = v
        del payload['ubicacion']
    r = requests.post(f"{API}/incidents", json=payload)
    print("INCIDENT", payload, r.status_code, r.text)

# Comentarios
try:
    with open("seed_comments.json") as f:
        comments = json.load(f)
    for c in comments:
        r = requests.post(f"{API}/incidents/{c['incident_id']}/comments", json={
            "comentario": c["comentario"],
            "agregado_por": c["agregado_por"],
            "timestamp": c["timestamp"]
        })
        print("COMMENT", c["incident_id"], r.status_code, r.text)
except Exception as e:
    print("No hay seed_comments.json o error =>", e)

# Eventos
try:
    with open("seed_events.json") as f:
        events = json.load(f)
    for ev in events:
        r = requests.post(f"{API}/incidents/{ev['incident_id']}/events", json={
            "tipo_evento": ev["tipo_evento"],
            "detalles": ev["detalles"],
            "timestamp": ev["timestamp"]
        })
        print("EVENT", ev["incident_id"], ev["tipo_evento"], r.status_code, r.text)
except Exception as e:
    print("No hay seed_events.json o error =>", e)

# Attachments
try:
    with open("seed_attachments.json") as f:
        attachments = json.load(f)
    for att in attachments:
        payload = {
            "file": "c29tZWJhc2U2NCBkYXRh",  # dummy base64
            "filename": att["filename"]
        }
        r = requests.post(f"{API}/student/incidents/{att['incident_id']}/attachments", json=payload)
        print("ATTACHMENT", att["incident_id"], att["filename"], r.status_code, r.text)
except Exception as e:
    print("No hay seed_attachments.json o error =>", e)
