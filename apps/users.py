"""
TODO: CREATE FOLLOWING ENDPOINTS:

THIS IS FOR THE FRONTEND:
{
    id: '',
    email: ''
    first_name: 'Team Name',
    last_name: '',
    bio: 'Hi I work at Google',
    created_at: TIMESTAMP,
    last_updated: TIMESTAMP
}

'2011-11-04T00:05:23+04:00'

You'll get the user_id and email of the person who made the API call from the JWT

GET /user -> Return the information about the requesting user.

GET /user/verify?email={email@test.com} -> Return whether an account exists with the given email address.
Return the full user object if yes, otherwise give a 404 response error

POST /user -> Create the user. I'll give you this information in the POST BODY. First, check that the
email doesn't already exist in our system.
{
    email: ''
    first_name: 'Team Name',
    last_name: '',
    bio: 'Hi I work at Google'
}


PUT /user -> Update the user. You'll get the same body as the POST request
"""
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from apps.jwt import get_current_user_data
from apps.firebase import db

user_api = FastAPI()

class User(BaseModel):
    email: str
    first_name: str
    last_name: str
    bio: str
    id: str

# Get current user
@user_api.get("/")
def get_user(current_user: dict = Depends(get_current_user_data)):
    id = current_user.get("id")
    user_doc = db.collection(u'users').document(id).get()
    return user_doc.to_dict()

# Get user
@user_api.get("/verify")
def get_user(email):
    user_ref = db.collection(u'users')
    query_ref = user_ref.where(u'email', u'==', email)
    docs = query_ref.get()

    if len(docs) < 1:
        raise HTTPException(status_code=404, detail=f"{email} not found")

    user_doc = docs[0]
    user_data = user_doc.to_dict()
    user_data["id"] = user_doc.id
    return(user_data)


# Create user
@user_api.post("/")
def create_user(user_data: User):
    user_ref = db.collection(u'users')
    user_docs = user_ref.where(u'email', u'==', user_data.email).get()

    if len(user_docs) > 0:
        raise HTTPException(status_code=404, detail=f"{user_data.email} already exists")

    new_user = user_ref.document()
    new_user.set({
        u'first_name': user_data.first_name,
        u'last_name': user_data.last_name,
        u'email': user_data.email,
        u'bio': user_data.bio,
        u'id': new_user.id,
    })
    user_data.id = new_user.id
    return user_data

# Update user
@user_api.put("/")
def update_user(user_data: User):
    user_ref = db.collection(u'users').document(user_data.id)

    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail=f"{user_data.email} doesn't exist")
    
    user_ref.update({
        u'first_name': user_data.first_name,
        u'last_name': user_data.last_name,
        u'email': user_data.email,
        u'bio': user_data.bio, 
    }) 

    return user_data