import json
import os
import requests

# Usar variable de entorno o valor por defecto
API = os.environ.get(
    "API_ENDPOINT",
    "https://4f7f6il2j5.execute-api.us-east-1.amazonaws.com/dev"
)


def parse_body(response):
    """Devuelve (data, body) donde body ya viene como dict si se puede."""
    try:
        data = response.json()
    except Exception:
        return None, None

    body = data.get("body")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            pass
    return data, body


def login(user_id, password):
    payload = {"user_id": user_id, "password": password}
    r = requests.post(f"{API}/auth/login", json=payload)
    print("LOGIN", user_id, r.status_code, r.text)
    if r.status_code != 200:
        return None
    _, body = parse_body(r)
    if not isinstance(body, dict):
        return None
    # Intentar varias claves posibles para el token
    token = body.get("token") or body.get("access_token") or body.get("Authorization")
    return token


def main():
    # ----- Usuarios -----
    with open("seed_users.json") as f:
        users = json.load(f)

    user_passwords = {u["user_id"]: u["password"] for u in users}

    for u in users:
        r = requests.post(f"{API}/auth/register", json=u)
        print("USER", u["user_id"], r.status_code, r.text)

    # ----- Incidentes (student/incidents) -----
    with open("seed_incidents.json") as f:
        incidents = json.load(f)

    for inc in incidents:
        # El handler createIncident espera:
        #  tipo, descripcion, ubicacion (dict), urgencia
        #  y toma el reporter_id desde el token, no del body.
        payload = {
            "tipo": inc.get("tipo"),
            "descripcion": inc.get("descripcion"),
            "ubicacion": inc.get("ubicacion"),
            "urgencia": inc.get("urgencia"),
        }

        # Hacer login como el reporter_id si está definido en seed_users
        headers = {}
        reporter_id = inc.get("reporter_id")
        if reporter_id and reporter_id in user_passwords:
            token = login(reporter_id, user_passwords[reporter_id])
            if token:
                headers["Authorization"] = token

        r = requests.post(f"{API}/student/incidents", json=payload, headers=headers)
        print("INCIDENT", payload, r.status_code, r.text)

    # ----- Comentarios (staff/incidents/{id}/comment) -----
    try:
        with open("seed_comments.json") as f:
            comments = json.load(f)

        for c in comments:
            incident_id = c["incident_id"]
            author_id = c.get("agregado_por")

            headers = {}
            if author_id and author_id in user_passwords:
                token = login(author_id, user_passwords[author_id])
                if token:
                    headers["Authorization"] = token

            body = {
                "comentario": c["comentario"],
            }

            r = requests.post(
                f"{API}/staff/incidents/{incident_id}/comment",
                json=body,
                headers=headers,
            )
            print("COMMENT", incident_id, r.status_code, r.text)
    except Exception as e:
        print("No hay seed_comments.json o error =>", e)

    # ----- Eventos -----
    # Ya no existe un endpoint POST para crear eventos manualmente,
    # ahora se generan desde las propias Lambdas (updateStatus, assignDepartment, addComment).
    # Por eso no intentamos seedear eventos vía HTTP aquí.
    print("Eventos no se generan vía seeder HTTP en esta versión (solo lectura por API).")

    # ----- Attachments (opcional, si existe seed_attachments.json) -----
    try:
        with open("seed_attachments.json") as f:
            attachments = json.load(f)

        for att in attachments:
            incident_id = att["incident_id"]
            filename = att["filename"]

            # Por simplicidad, usamos el mismo usuario que se definió como reporter_id
            # en seed_incidents, si coincide.
            reporter_id = att.get("reporter_id")
            headers = {}
            if reporter_id and reporter_id in user_passwords:
                token = login(reporter_id, user_passwords[reporter_id])
                if token:
                    headers["Authorization"] = token

            payload = {
                "file": "c29tZWJhc2U2NCBkYXRh",  # dummy base64
                "filename": filename,
            }

            r = requests.post(
                f"{API}/student/incidents/{incident_id}/attachments",
                json=payload,
                headers=headers,
            )
            print("ATTACHMENT", incident_id, filename, r.status_code, r.text)
    except Exception as e:
        print("No hay seed_attachments.json o error =>", e)


if __name__ == "__main__":
    main()

