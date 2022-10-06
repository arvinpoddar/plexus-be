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
from apps.users import User, create_user

team_api = FastAPI()

class Team(BaseModel):
    name: str
    users: list
    id: str

# Get all teams of user
@team_api.get("/")
def get_teams(current_user: dict = Depends(get_current_user_data)):
    id = str(current_user.get('id'))
    # id = "lcxzDloR0DehARLVNyu1"
    temp = "users.a" + id
    teams = db.collection(u'teams').order_by(temp).get()
    print(teams)
    team_list = []
    for team in teams:
        team_list.append({"id": team.id, "name": team.get("name")})

    return team_list

# Return data about a single team
@team_api.get("/{team_id}")
def get_team(team_id):
    team_doc = db.collection(u'teams').document(team_id)
    team_data = team_doc.get().to_dict()
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
def delete_team(team_id):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    if team.exists:
        team_doc.delete()
    else:
        raise HTTPException(status_code=404, detail=f"{team_id} doesn't exist")
    name = team.to_dict().get("name")

    return f"{name} deleted"

# Create a team by passing in Team object
# TODO: Known issue: User object with already used email but no ID will error (discuss correct handling)
@team_api.post("/")
def create_team(team_data: Team):
    teams_ref = db.collection(u'teams')

    # Check if team exists already
    team_docs = teams_ref.where(u'name', u'==', team_data.name).get()
    if len(team_docs) > 0:
        raise HTTPException(status_code=404, detail=f"{team_data.name} already exists")
    
    # Add users to team
    user_dict = {}
    for user in team_data.users:
        # First, check if user id is not empty
        # If it is, create new user
        id = user.get('id')
        if id == "":
            new_user = User(
                email=user.get("email"),
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                bio=user.get("bio"),
                id=user.get("id"),
            )
            new_user = create_user(new_user)
            id = new_user.id
        # Else, make sure that the id is valid
        else:
            user_doc = db.collection(u'users').document(id).get()
            if not user_doc.exists:
                raise HTTPException(status_code=404, detail=f"{id} is invalid or not registered")

        user_dict[id] = {"role": "member"}
    
    new_team = teams_ref.document()
    new_team.set({
        u'name': team_data.name,
        u'users': user_dict,
        u'id': new_team.id,
    })
    team_data.id = new_team.id

    return team_data

# TODO: Currently this is for verification of current user
# Additional functionality will depend on other specifics
@team_api.put("/{team_id}")
def verify_admin(team_id, current_user: dict = Depends(get_current_user_data)):
    email = current_user.get("email")
    team_doc = db.collection(u'teams').document(team_id)
    team_data = team_doc.get().to_dict()
    team_users = team_data.pop('users', None)
    if team_id in team_users:
        if team_users.get(team_id).get("role") not in ["admin", "owner"]:
            raise HTTPException(status_code=404, detail=f"{email} doesn't have permission for this team")
    else:
        raise HTTPException(status_code=404, detail=f"{email} not in team")

    return f"{email} has permission for this team"