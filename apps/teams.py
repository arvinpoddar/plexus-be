"""
https://fastapi.tiangolo.com/tutorial/path-params/


THIS IS WHAT A TEAM SHOULD LOOK LIKE FOR THE FRONTEND:
Team:
{
    id: 'uniquestring'
    name: 'Team Name',
    users: [],
    documents: [],
    edges: [] - should be a collection,
    created_at: TIMESTAMP,
    last_updated: TIMESTAMP
}

TODO: CREATE FOLLOWING ENDPOINTS:

You'll get the user_id and email of the person who made the API call from the JWT

GET /teams -> Get all teams for the user

POST /teams -> Create a new team (I'll give you a name and an array of users)
Each user will have an email and a role. You also need to add the user who created
this team as an owner. The post body will look something like this:
{
    name: '',
    users: [list of user objects, with system IDs]
}
This endpoint will need to make sure every user id exists.

GET /teams/:team-id -> Return the team object (just name and users right now). 
Make sure that the requesting user is in the team.

PUT /teams/:team-id -> First, make sure the ID of the current user is that of an owner/admin
in the requested team. This is to update whatever is in the team. We can use this endpoint to
edit team name, or edit which users are inside of the team and their roles.

DELETE /teams/:team-id -> Delete the entire team.

DELETE /teams/:team-id/user/:user-id -> Deletes a user from a particular team. Do not delete from our system.
First, verify that the requesting user is an admin/owner of the team. Then, make sure the user to delete 
is in the team.
"""

"""
TEAM ROLES:
owner
admin
member
"""

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from apps.jwt import get_current_user_data
from apps.firebase import db
from vars.roles import Roles

team_api = FastAPI()

# Get all teams of user
@team_api.get("/")
def get_teams(current_user: dict = Depends(get_current_user_data)):
    id = str(current_user.get('id'))
    teams = db.collection(u'teams').order_by("users." + id).get()
    return [{"id": team.id, "name": team.get("name")} for team in teams]

# Return data about a single team


@team_api.get("/{team_id}")
def get_team(team_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)
    team_data = team.to_dict()
    users_dict = team_data.pop('users', None)
    if users_dict == None:
        return team_data

    team_users = []
    for k, v in users_dict.items():
        user_doc = db.collection(u'users').document(k).get()
        user_dict = user_doc.to_dict()
        user_dict.update(v)
        team_users.append(user_dict)
    team_data["users"] = team_users

    return team_data

# Delete a team


@team_api.delete("/{team_id}")
def delete_team(team_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    
    verify_user(team, current_user["id"], Roles.ADMIN)
    if not team.exists:
        raise HTTPException(status_code=404, detail=f"{team_id} doesn't exist")

    team_doc.delete()
    name = team.to_dict().get("name")

    return f"{name} deleted"

# Create a team by passing in Team object


class CreateTeamRequest(BaseModel):
    id: str
    name: str
    description: str


@team_api.post("/")
def create_team(team_data: CreateTeamRequest, current_user: dict = Depends(get_current_user_data)):
    teams_ref = db.collection(u'teams')
    user_dict = {}
    user_dict[current_user['id']] = {"role": Roles.ADMIN.name}

    new_team = teams_ref.document()
    new_team.set({
        u'id': new_team.id,
        u'name': team_data.name,
        u'description': team_data.description,
        u'users': user_dict,
        u'documents': {},
        u'edges': {},
    })
    team_data.id = new_team.id

    return team_data


@team_api.put("/{team_id}")
def update_team(team_id, team_data: CreateTeamRequest, current_user: dict = Depends(get_current_user_data)):
    teams_ref = db.collection(u'teams')
    team_doc = teams_ref.document(team_id)
    
    verify_user(team_doc.get(), current_user["id"], Roles.ADMIN)
    if not team_doc.get().exists:
        raise HTTPException(
            status_code=404, detail=f"Team {team_id} doesn't exist")

    team_doc.update({
        u'name': team_data.name,
        u'description': team_data.description,
    })

    return team_doc.get().to_dict()


def insert_or_update_team_user(team_id, requesting_id, request):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()

    verify_user(team, requesting_id, Roles.ADMIN)

    team_data = team.to_dict()
    team_users = team_data.pop('users', {})

    if requesting_id == request.id:
        raise HTTPException(
            status_code=403, detail=f"{requesting_id} cannot edit itself")

    inserting_user = db.collection(u'users').document(request.id).get()
    if not inserting_user.exists:
        raise HTTPException(
            status_code=404, detail=f"User {request.id} doesn't exist")

    team_users[request.id] = {"role": request.role.lower()}

    team_doc.update({
        u'users': team_users,
    })
    inserting_user = db.collection(u'users').document(request.id).get()
    return inserting_user.to_dict()


class InsertUserRequest(BaseModel):
    id: str
    role: str


@team_api.get("/{team_id}/users")
def get_team(team_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()

    verify_user(team, current_user["id"], Roles.MEMBER)

    team_data = team.to_dict()
    users_dict = team_data.pop('users', None)

    if users_dict == None:
        return []

    team_users = []
    for k, v in users_dict.items():
        user_doc = db.collection(u'users').document(k).get()
        user_dict = user_doc.to_dict()
        user_dict.update(v)
        team_users.append(user_dict)

    return team_users


@team_api.post("/{team_id}/users")
def post_team_user(team_id, request: InsertUserRequest, current_user: dict = Depends(get_current_user_data)):
    return insert_or_update_team_user(team_id, current_user["id"], request)


@team_api.put("/{team_id}/users/{user_id}")
def put_team_user(team_id, request: InsertUserRequest, current_user: dict = Depends(get_current_user_data)):
    return insert_or_update_team_user(team_id, current_user["id"], request)


@team_api.delete("/{team_id}/users/{user_id}")
def delete_team_user(team_id, user_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()

    verify_user(team, current_user["id"], Roles.ADMIN)

    team_data = team.to_dict()
    team_users = team_data.pop('users', {})

    requesting_id = current_user["id"]
    if requesting_id == user_id:
        raise HTTPException(
            status_code=403, detail=f"{requesting_id} cannot edit itself")

    deleted_user = db.collection(u'users').document(user_id).get()
    if not deleted_user.exists:
        raise HTTPException(
            status_code=404, detail=f"User {user_id} doesn't exist")

    team_users.pop(user_id)
    team_doc.update({
        u'users': team_users,
    })

    return deleted_user.to_dict()


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