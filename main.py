from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes, chatHistoryRoutes, chatRoutes, commentSuggestionRoutes, Router,validateContentRoutes,chatRoutesTharundi
from routes.errorRoutes import router as error_router

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your auth routes with prefix
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])

# Include API routes
app.include_router(chatHistoryRoutes.router, prefix="/chatHistory")
app.include_router(chatRoutes.router, prefix="/chats")
app.include_router(Router.router)
app.include_router(commentSuggestionRoutes.router, prefix='/commentCode')
app.include_router(validateContentRoutes.router, prefix="/validate")
app.include_router(chatRoutesTharundi.router)
app.include_router(error_router)


@app.get("/")
async def root():
    return {"message": "System is running"}


