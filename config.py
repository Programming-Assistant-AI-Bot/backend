# config.py

from dotenv import load_dotenv
import os

# Load from .env
load_dotenv()

# Now read env vars
MONGO_URL = os.getenv("MONGO_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

print (f"Mongo URL: {MONGO_URL}")
