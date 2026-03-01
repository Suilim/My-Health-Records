import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import streamlit as st

if not firebase_admin._apps:
    key_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://an-an-5cf88-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })