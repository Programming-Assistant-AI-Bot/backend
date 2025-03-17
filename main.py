from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chatHistoryRoutes, chatRoutes

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chatHistoryRoutes.router, prefix="/chatHistory")
app.include_router(chatRoutes.router, prefix="/chats")

@app.get("/")
async def root():
    return {"message": "Asset Tracking System API is running!"}