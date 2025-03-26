"""
Facebook Webhook Application
Main entry point for the FastAPI application that handles Facebook webhooks.
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import db
from routes import router
from utils.config import Config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application
    
    Handles startup and shutdown events
    """
    # Startup logic
    db.init_default_page()  # Initialize default page with the token
    yield
    # Shutdown logic
    db.close()

# Initialize FastAPI app
app = FastAPI(
    title="Facebook Webhook API",
    description="API for handling Facebook webhook events",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)