import json
import requests

API = "https://<tu-api-id>.execute-api.us-east-1.amazonaws.com/dev"

with open("seed_users.json") as f:
    users = json.load(f)

for u in users:
    r = requests.post(f"{API}/auth/register", json=u)
    print(u["user_id"], r.status_code, r.text)
