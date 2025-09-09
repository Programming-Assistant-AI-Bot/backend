
from pymongo import MongoClient

def get_db():
    try:
        client = MongoClient("mongodb+srv://dbUser:projectTest123@cluster1.jp9dn.mongodb.net/")
        db = client["Chatbot"]
      
        print("Connected to MongoDB")
    except Exception as e:
       print(f"Error connecting to MongoDB: {e}")

get_db()