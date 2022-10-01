"""
https://fastapi.tiangolo.com/tutorial/path-params/


THIS IS WHAT A TEAM SHOULD LOOK LIKE FOR THE FRONTEND:
Team:
{
    id: 'uniquestring'
    name: 'Team Name',
    users: [],
    documents: [],
    edges: [],
    created_at: TIMESTAMP,
    last_updated: TIMESTAMP
}

TODO: CREATE FOLLOWING ENDPOINTS:

You'll get the user_id and email of the person who made the API call from the JWT

GET /teams -> Get all teams for the user

POST /teams -> Create a new team (I'll give you a name and an array of users)
Each user will have an email and a role. You also need to add the user who created
this team as an owner.

PUT /teams/:team-id -> First, make sure the ID of the current user is that of an owner/admin
in the requested team. This is to update whatever is in the team. We can use this endpoint to
edit team name, or edit which users are inside of the team and their roles.

DELETE /teams/:team-id -> Delete the entire team.
"""

"""
TEAM ROLES:
owner
admin
member
"""