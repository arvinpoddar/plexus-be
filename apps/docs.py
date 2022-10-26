from fastapi import  APIRouter, Depends, HTTPException
from pydantic import BaseModel
from apps.jwt import get_current_user_data
from apps.firebase import db
from vars.roles import Roles
from vars.helpers import verify_user

document_router = APIRouter(prefix="/{team_id}/documents")

@document_router.get("/")
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

@document_router.get("/{doc_id}")
def get_document(team_id, doc_id, current_user: dict = Depends(get_current_user_data)):
    team_doc = db.collection(u'teams').document(team_id)
    team = team_doc.get()
    verify_user(team, current_user["id"], Roles.MEMBER)


    document = db.collection('teams').document(team_id).collection('documents').document(doc_id).get()
    
    if not document.exists:
        raise HTTPException(
            status_code=404, detail=f"Document {doc_id} doesn't exist")
    
    return document.to_dict()

class DocumentRequest(BaseModel):
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
    })
    doc.id = new_doc.id
    return doc

@document_router.put("/{doc_id}")
def update_document(team_id, doc: DocumentRequest, doc_id, current_user: dict = Depends(get_current_user_data)):
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

    return f"{doc_dict['name']} deleted"