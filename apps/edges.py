from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from apps.jwt import get_current_user_data
from apps.firebase import db
from vars.roles import Roles
from vars.helpers import verify_user, create_edge_id

edge_router = APIRouter(prefix="/{team_id}/edges")

@edge_router.get("/")
def get_edges(team_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    edge_col = db.collection('teams').document(team_id).collection('edges')
    doc_array = [edge.to_dict() for edge in edge_col.get()]

    return doc_array

class Edge(BaseModel):
    description: str
    x: str
    y: str
    id: str

@edge_router.post("/")
def create_edge(team_id, edge: Edge, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    docs_ref = db.collection('teams').document(team_id).collection('edges')
    new_id = create_edge_id(edge.x, edge.y)
    
    doc_ids = [doc.id for doc in db.collection('teams').document(team_id).collection('documents').select('').get()]
    if not (edge.x in doc_ids and edge.y in doc_ids):
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
        u'x': edge.x,
        u'y': edge.y,
        u'id': new_id,
    })
    edge.id = new_id
    return edge

@edge_router.put("/{edge_id}")
def update_edge(team_id, edge: Edge, edge_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.ADMIN)

    doc_ref = db.collection('teams').document(team_id).collection('edges').document(edge_id)

    doc_ref.update({
        u'description': edge.description,
    })

    return edge

@edge_router.delete("/{edge_id}")
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