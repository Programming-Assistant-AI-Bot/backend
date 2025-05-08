from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

DB_URL = os.getenv("URL")

client = AsyncIOMotorClient(DB_URL)

Chatbot = client.Chatbot

message_collection = Chatbot.get_collection("Messages")
session_collection = Chatbot.get_collection("sessions")
session_collection.create_index("sessionId",unique=True)

try:
    client.admin.command("ping")
    print("✅ MongoDB connection successful!")
except Exception as e:
    print("❌ MongoDB connection failed!", e)
