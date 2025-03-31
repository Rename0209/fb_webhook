"""
Configuration Module
This module handles loading and providing configuration settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the application"""
    
    # Facebook API settings
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "your_verify_token")
    PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "")
    PAGE_ID = os.getenv("PAGE_ID", "")
    
    # MongoDB settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "facebook_webhook")
    MONGODB_COLLECTION_LOGS = os.getenv("MONGODB_COLLECTION_LOGS", "webhook_logs")
    MONGODB_COLLECTION_PAGES = os.getenv("MONGODB_COLLECTION_PAGES", "pages")
    MONGODB_COLLECTION_NOTIFICATION = os.getenv("MONGODB_COLLECTION_NOTIFICATION", "notification_messages")
    MONGODB_COLLECTION_ADDRESSES = os.getenv("MONGODB_COLLECTION_ADDRESSES", "addresses")
    
    # Server settings
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", "8000"))
    
    # Backend forwarding settings
    BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "http://localhost:4000/api/webhook")
    FORWARD_TIMEOUT = int(os.getenv("FORWARD_TIMEOUT", "30"))
    ENABLE_FORWARDING = os.getenv("ENABLE_FORWARDING", "true").lower() == "true"
    
    @classmethod
    def get_all(cls):
        """Get all configuration settings as dictionary"""
        return {
            "VERIFY_TOKEN": cls.VERIFY_TOKEN,
            "PAGE_ID": cls.PAGE_ID,
            "MONGODB_URI": cls.MONGODB_URI,
            "MONGODB_DB": cls.MONGODB_DB,
            "MONGODB_COLLECTION_LOGS": cls.MONGODB_COLLECTION_LOGS,
            "MONGODB_COLLECTION_PAGES": cls.MONGODB_COLLECTION_PAGES,
            "MONGODB_COLLECTION_NOTIFICATION": cls.MONGODB_COLLECTION_NOTIFICATION,
            "MONGODB_COLLECTION_ADDRESSES": cls.MONGODB_COLLECTION_ADDRESSES,
            "HOST": cls.HOST,
            "PORT": cls.PORT,
            "BACKEND_SERVER_URL": cls.BACKEND_SERVER_URL,
            "FORWARD_TIMEOUT": cls.FORWARD_TIMEOUT,
            "ENABLE_FORWARDING": cls.ENABLE_FORWARDING
        } 