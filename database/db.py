from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

DB_URL = os.getenv("DB_URL")

client = AsyncIOMotorClient(DB_URL)

Chatbot = client.Chatbot

message_collection = Chatbot["Messages"]