from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your auth routes with prefix
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])

