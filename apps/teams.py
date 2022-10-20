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
from vars.status import Status

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
    user_dict[current_user['id']] = {"role": Roles.OWNER.name.lower()}

    new_team = teams_ref.document()
    new_team.set({
        u'id': new_team.id,
        u'name': team_data.name,
        u'description': team_data.description,
        u'users': user_dict,
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



"""
Document Endpoints

"""

@team_api.get("/{team_id}/documents")
def get_all_documents(team_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    document_col = db.collection('teams').document(team_id).collection('documents')
    doc_array = [doc.to_dict() for doc in document_col.get()]
    for doc in doc_array:
        if len(doc['content']) > 150:
            doc['content'] = doc['content'][:150]
    return doc_array

@team_api.get("/{team_id}/documents/{doc_id}")
def get_document(team_id, doc_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    document = db.collection('teams').document(team_id).collection('documents').document(doc_id).get()
    
    if not document.exists:
        raise HTTPException(
            status_code=404, detail=f"Document {doc_id} doesn't exist")
    
    return document.to_dict()

class Document(BaseModel):
    name: str
    status: str
    content: str
    id : str

@team_api.post("/{team_id}/documents")
def create_document(team_id, doc: Document, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    docs_ref = db.collection('teams').document(team_id).collection('documents')
    new_doc = docs_ref.document()
    new_doc.set({
        u'author': current_user["id"],
        u'content': doc.content,
        u'status': doc.status,
        u'name': doc.name,
        u'id': new_doc.id,
    })
    doc.id = new_doc.id
    return doc

@team_api.put("/{team_id}/documents/{doc_id}")
def update_document(team_id, doc: Document, doc_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.ADMIN)

    doc_ref = db.collection('teams').document(team_id).collection('documents').document(doc_id)
    if current_user["id"] != doc_ref.get().to_dict()['author']:
        raise HTTPException(
            status_code=403, detail=f"{current_user['id']} has no permission for this document")

    doc_ref.update({
        u'content': doc.content,
        u'status': doc.status,
        u'name': doc.name,
    })

    return doc

@team_api.delete("/{team_id}/documents/{doc_id}")
def delete_document(team_id, doc_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    doc_ref = db.collection('teams').document(team_id).collection('documents').document(doc_id)
    doc = doc_ref.get()

    verify_user(team, current_user['id'], Roles.MEMBER)
    if not doc.exists:
        raise HTTPException(
            status_code=404, detail=f"{doc_id} doesn't exist"
        )
    doc_dict = doc.to_dict()

    if current_user["id"] != doc_dict['author']:
        verify_user(team, current_user['id'], Roles.ADMIN)

    doc_ref.delete()

    return f"{doc_dict['name']} deleted"

"""
Edge Endpoints

"""

@team_api.get("/{team_id}/edges")
def get_edges(team_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    edge_col = db.collection('teams').document(team_id).collection('edges')
    doc_array = [edge.to_dict() for edge in edge_col.get()]

    return doc_array

class Edge(BaseModel):
    description: str
    frm: str
    to: str
    id: str

@team_api.post("/{team_id}/edges")
def create_edge(team_id, edge: Edge, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    docs_ref = db.collection('teams').document(team_id).collection('edges')
    new_id = edge.frm + edge.to if edge.frm.lower() < edge.to.lower() else edge.to + edge.frm
    
    doc_ids = [doc.id for doc in db.collection('teams').document(team_id).collection('documents').select('').get()]
    if not (edge.frm in doc_ids and edge.to in doc_ids):
        raise HTTPException(
            status_code=404, detail="Documents don't exist"
        ) 

    if new_id in [doc.id for doc in docs_ref.select('').get()]:
        raise HTTPException(
            status_code=404, detail="Edge already exists"
        )

    new_doc = docs_ref.document(new_id)
    new_doc.set({
        u'description': edge.description,
        u'from': edge.frm,
        u'to': edge.to,
        u'id': new_id,
    })
    edge.id = new_id
    return edge

@team_api.put("/{team_id}/edges/{edge_id}")
def update_edge(team_id, edge: Edge, edge_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.ADMIN)

    doc_ref = db.collection('teams').document(team_id).collection('edges').document(edge_id)

    doc_ref.update({
        u'description': edge.description,
    })

    return edge

@team_api.delete("/{team_id}/edges/{edge_id}")
def delete_edge(team_id, edge_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    edge_ref = db.collection('teams').document(team_id).collection('edges').document(edge_id)
    edge = edge_ref.get()

    verify_user(team, current_user['id'], Roles.MEMBER)
    if not edge.exists:
        raise HTTPException(
            status_code=404, detail=f"{edge_id} doesn't exist"
        )
    edge_dict = edge.to_dict()

    edge_ref.delete()

    return f"{edge_dict['id']} deleted"