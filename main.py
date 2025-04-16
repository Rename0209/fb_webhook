"""
Facebook Webhook Application
Main entry point for the FastAPI application that handles Facebook webhooks.
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import router
from utils.config import Config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application
    
    Handles startup and shutdown events
    """
    # Initialize database on startup
    from database import db
    
    yield
    
    # Cleanup on shutdown
    db.close()

# Initialize FastAPI app
app = FastAPI(
    title="Facebook Webhook API",
    description="API for handling Facebook webhook events",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(Config.PORT), 
        reload=True
    )