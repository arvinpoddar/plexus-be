from fastapi import HTTPException
from vars.roles import Roles

def verify_user(team, uid, req_role):
    if not team.exists:
        raise HTTPException(
            status_code=404, detail=f"Team doesn't exist")
    users = team.to_dict()['users']
    user = users.get(uid, None)
    user_role = user['role']

    if not user_role or Roles[user_role.upper()].value < req_role.value:
        raise HTTPException(
            status_code=403, detail=f"{uid} has no permission for this team")

def create_edge_id(x: str, y: str):
    edges = sorted([x, y])
    return "-".join(edges)