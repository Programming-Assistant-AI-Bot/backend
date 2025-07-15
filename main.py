from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- STEP 1: ONLY import the database client and the ONE router we need ---
# We are not importing chatRoutes or any other router to avoid errors.
from database.db import client
from routes.errorRoutes import router as error_router

# This lifespan function will handle startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("--- Application starting up for error checking... ---")
    app.mongodb_client = client
    try:
        # Test the connection
        await app.mongodb_client.admin.command("ping")
        print("✅ MongoDB connection successful!")
    except Exception as e:
        print(f"❌ MongoDB connection failed! {e}")
    
    yield
    
    # Code to run on shutdown
    print("--- Application shutting down... ---")
    app.mongodb_client.close()

# --- STEP 2: Create the app using the lifespan function ---
app = FastAPI(lifespan=lifespan)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STEP 3: ONLY include the error checking router ---
# This ensures no other part of the application is loaded.
app.include_router(error_router)


@app.get("/")
async def root():
    return {"message": "Error Checker API is running"}
