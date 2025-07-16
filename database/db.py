from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables from .env file
load_dotenv()


DB_URL = os.getenv("DB_URL")
print(DB_URL)


# --- This is a critical check to make sure the .env file is being read ---
if not DB_URL:
    raise ValueError("Could not find MONGODB_URI in the .env file. Please ensure it exists and is correct.")

print(f"--- Connecting to MongoDB with URI: {DB_URL} ---")

# Create async MongoDB client
client = AsyncIOMotorClient(DB_URL)

# Access the Chatbot database
Chatbot = client.Chatbot

message_collection = Chatbot.get_collection("Messages")

session_collection = Chatbot.get_collection("sessions")
session_collection.create_index("sessionId",unique=True)

user_collection = Chatbot.get_collection("user")

file_collection = Chatbot.get_collection("files")
file_collection.create_index("fileId",unique=True)

try:
    client.admin.command("ping")
    print("✅ MongoDB connection successful!")
except Exception as e:
    print("❌ MongoDB connection failed!", e)
