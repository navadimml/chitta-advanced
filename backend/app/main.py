"""
Chitta Backend - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

from app.api.routes import router
from app.core.app_state import app_state

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Chitta API",
    description="API for Chitta child development assessment platform",
    version="1.0.0"
)

# CORS
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")

# Startup/Shutdown events
@app.on_event("startup")
async def startup():
    logger.info("🚀 Starting Chitta Backend...")
    await app_state.initialize()
    logger.info("✅ Chitta Backend ready!")

@app.on_event("shutdown")
async def shutdown():
    logger.info("👋 Shutting down Chitta Backend...")
    await app_state.shutdown()

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "initialized": app_state.initialized
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
