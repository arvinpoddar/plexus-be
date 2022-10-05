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
from apps.firebase import db_app, db

team_api = FastAPI()

@team_api.get("/")
def get_teams(current_user: dict = Depends(get_current_user_data)):
        return "hi"