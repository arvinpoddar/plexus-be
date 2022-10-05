import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials

cred = credentials.Certificate('/home/parth/firebase.json')

db_app = firebase_admin.initialize_app(cred)
db = firestore.client()