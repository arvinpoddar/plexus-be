from fastapi import  APIRouter, Depends, HTTPException
from pydantic import BaseModel
from apps.jwt import get_current_user_data
from apps.firebase import db
from vars.roles import Roles
from vars.helpers import verify_user, create_edge_id
from firebase_admin import firestore
from vars.similarity import find_similarity

document_router = APIRouter(prefix="/{team_id}/documents")

@document_router.get("/")
def get_all_documents(team_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    document_col = db.collection('teams').document(team_id).collection('documents')
    doc_array = [doc.to_dict() for doc in document_col.get()]
    for doc in doc_array:
        user_doc = db.collection(u'users').document(doc['author']).get()
        doc['author'] = user_doc.to_dict()

        if len(doc['content']) > 100:
            doc['content'] = doc['content'][:100] + '...'

    return doc_array

@document_router.get("/{doc_id}")
def get_document(team_id, doc_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    document = db.collection('teams').document(team_id).collection('documents').document(doc_id).get()
    
    if not document.exists:
        raise HTTPException(
            status_code=404, detail=f"Document {doc_id} doesn't exist")
    
    ret = document.to_dict()
    user_doc = db.collection(u'users').document(ret['author']).get()
    ret['author'] = user_doc.to_dict()

    return ret

@document_router.get("/{doc_id}/suggestions")
def get_doc_similarities(team_id, doc_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()

    verify_user(team, current_user["id"], Roles.MEMBER)
    similarities = find_similarity(doc_id, team_id)

    edge_col = db.collection('teams').document(team_id).collection('edges')
    edges = [edge.to_dict()["id"] for edge in edge_col.get()]

    res = []

    for doc in similarities:
        
        new_edge = create_edge_id(doc_id, doc[0])
        if new_edge in edges or doc_id == doc[0]:
            continue

        temp = {
            "id" : new_edge,
            "x" : get_document(team_id, doc_id, current_user),
            "y" : get_document(team_id, doc[0], current_user),
            "description" : "Created from suggestions",
            "similarity" : doc[1],
        }
        res.append(temp)

        if len(res) > 2 or temp["similarity"] < .3:
            break

    return res

class DocumentRequest(BaseModel):
    id: str
    name: str
    status: str
    content: str

@document_router.post("/")
def create_document(team_id, doc: DocumentRequest, current_user: dict = Depends(get_current_user_data)):
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
        u'creation_time': firestore.SERVER_TIMESTAMP,
        u'last_updated': firestore.SERVER_TIMESTAMP
    })
    doc.id = new_doc.id

    ret = docs_ref.document(doc.id).get().to_dict()
    user_doc = db.collection(u'users').document(ret['author']).get()
    ret['author'] = user_doc.to_dict()

    return ret

@document_router.put("/{doc_id}")
def update_document(team_id, doc: DocumentRequest, doc_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)

    doc_ref = db.collection('teams').document(team_id).collection('documents').document(doc_id)
    if current_user["id"] != doc_ref.get().to_dict()['author']:
        raise HTTPException(
            status_code=403, detail=f"{current_user['id']} has no permission for this document")

    doc_ref.update({
        u'content': doc.content,
        u'status': doc.status,
        u'name': doc.name,
        u'last_updated': firestore.SERVER_TIMESTAMP
    })

    ret = doc_ref.get().to_dict()
    user_doc = db.collection(u'users').document(ret['author']).get()
    ret['author'] = user_doc.to_dict()

    return ret

@document_router.delete("/{doc_id}")
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

    edge_col = db.collection('teams').document(team_id).collection('edges')
    for edge in edge_col.get():
        d = edge.to_dict()
        if doc_id in [d['x'], d['y']]:
            edge_col.document(d['id']).delete()

    return f"{doc_dict['name']} deleted"