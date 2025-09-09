# database/mongodb.py
from pymongo import MongoClient
from config import MONGO_URL

# Create the MongoDB client
client = MongoClient("mongodb+srv://dbUser:projectTest123@cluster1.jp9dn.mongodb.net/")

# Connect to a specific database
db = client["Chatbot"] # replace with your actual DB name if different

# Define the collection for user authentication
user_collection = db["user"]


