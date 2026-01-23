import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

if not firebase_admin._apps:
    cred = credentials.Certificate('an-an-5cf88-firebase-adminsdk-fbsvc-0362250554.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://an-an-5cf88-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })