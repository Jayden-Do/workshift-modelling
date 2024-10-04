from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
# Create a new client and connect to the server
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["database"]


def get_database():
    return db
