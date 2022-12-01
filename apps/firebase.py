import os
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"../firebase_creds.json")
cred = credentials.Certificate(file_path)

db_app = firebase_admin.initialize_app(cred)
db = firestore.client()