from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment
DB_URL = os.getenv("MONGODB_URI")

# --- This is a critical check to make sure the .env file is being read ---
if not DB_URL:
    raise ValueError("Could not find MONGODB_URI in the .env file. Please ensure it exists and is correct.")

print(f"--- Connecting to MongoDB with URI: {DB_URL} ---")

# Create async MongoDB client
client = AsyncIOMotorClient(DB_URL)

# Access the Chatbot database
Chatbot = client.Chatbot

# Export collections so other files can use them
message_collection = Chatbot.get_collection("Messages")
session_collection = Chatbot.get_collection("sessions")
file_collection = Chatbot.get_collection("files")
