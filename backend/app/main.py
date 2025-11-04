"""
Chitta FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="Chitta API",
    description="AI-powered child development screening platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allows frontend to communicate with backend
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "Chitta API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "chitta-backend"
    }


# TODO: Add API routes
# Example structure:
# from app.api.v1 import messages, videos, reports
# app.include_router(messages.router, prefix="/api/v1", tags=["messages"])
# app.include_router(videos.router, prefix="/api/v1", tags=["videos"])
# app.include_router(reports.router, prefix="/api/v1", tags=["reports"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
