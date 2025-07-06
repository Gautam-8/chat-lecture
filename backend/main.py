from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.routers import lectures, chat, auth
from backend.database import init_db

app = FastAPI(title="Chat with your Lecture", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(lectures.router, prefix="/api/lectures", tags=["lectures"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 