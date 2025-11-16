def get_user_from_request(event):
    claims = event["requestContext"]["authorizer"]["claims"]

    # cognito:groups sometimes comes like "['STAFF']" or just "STAFF"
    groups_raw = claims.get("cognito:groups", "")
    
    if isinstance(groups_raw, str):
        groups = groups_raw.replace("[", "").replace("]", "").replace("'", "").split(",")
        groups = [g.strip().lower() for g in groups]
    else:
        groups = [g.lower() for g in groups_raw]

    return {
        "user_id": claims["sub"],
        "email": claims.get("email"),
        "name": claims.get("name", ""),
        "role": groups[0] if len(groups) > 0 else None,
        "department": claims.get("custom:department", None)
    }
