"""
Facebook Webhook Application
Main entry point for the FastAPI application that handles Facebook webhooks.
"""
import asyncio
import os
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
    # Initialize database and default page on startup
    from database import db
    
    # Initialize default page if configured
    if hasattr(Config, 'PAGE_ID') and Config.PAGE_ID:
        await db.init_default_page()
    
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
    port = int(os.getenv("PORT", 8000))  # Lấy PORT từ biến môi trường, mặc định 8000
    uvicorn.run(app, host="0.0.0.0", port=port)