from typing import Dict, Any
import time
import json
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from utils.config import Config
import asyncio
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

class Database:
    def __init__(self):
        self._connection_ready = False
        self._max_retries = 3
        self._retry_delay = 5  # seconds
        self._initialize_connections()

    def _initialize_connections(self):
        """Initialize MongoDB connections with retry mechanism"""
        try:
            # Use Motor for async operations
            self.async_client = AsyncIOMotorClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,  # 5 seconds timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10
            )
            self.async_db = self.async_client[Config.MONGODB_DB]
            self.async_logs_collection = self.async_db[Config.MONGODB_COLLECTION_LOGS]
            self.async_pages_collection = self.async_db[Config.MONGODB_COLLECTION_PAGES]
            self.async_notification_collection = self.async_db[Config.MONGODB_COLLECTION_NOTIFICATION]
            self.async_addresses_collection = self.async_db[Config.MONGODB_COLLECTION_ADDRESSES]
            
            # Keep PyMongo for sync operations
            self.client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10
            )
            self.db = self.client[Config.MONGODB_DB]
            self.logs_collection = self.db[Config.MONGODB_COLLECTION_LOGS]
            self.pages_collection = self.db[Config.MONGODB_COLLECTION_PAGES]
            self.notification_collection = self.db[Config.MONGODB_COLLECTION_NOTIFICATION]
            self.addresses_collection = self.db[Config.MONGODB_COLLECTION_ADDRESSES]
            
            # Create indexes
            self.logs_collection.create_index("time_id")
            self.pages_collection.create_index("page_id", unique=True)
            self.notification_collection.create_index("data.notification_messages_token")
            self.addresses_collection.create_index("sender_id")
            
            print(f"[INFO] Successfully connected to MongoDB: {Config.MONGODB_URI}")
            self._connection_ready = True
            
        except Exception as e:
            print(f"[ERROR] MongoDB connection failed: {str(e)}")
            self._set_default_values()
            self._connection_ready = False

    def _set_default_values(self):
        """Set default values when connection fails"""
        self.async_client = None
        self.async_db = None
        self.async_logs_collection = None
        self.async_pages_collection = None
        self.async_notification_collection = None
        self.async_addresses_collection = None
        self.client = None
        self.db = None
        self.logs_collection = None
        self.pages_collection = None
        self.notification_collection = None
        self.addresses_collection = None

    async def _ensure_connection(self):
        """Ensure MongoDB connection is active"""
        if not self._connection_ready:
            for attempt in range(self._max_retries):
                try:
                    print(f"[INFO] Attempting to reconnect to MongoDB (attempt {attempt + 1}/{self._max_retries})")
                    self._initialize_connections()
                    if self._connection_ready:
                        print("[INFO] Successfully reconnected to MongoDB")
                        return True
                    await asyncio.sleep(self._retry_delay)
                except Exception as e:
                    print(f"[ERROR] Reconnection attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(self._retry_delay)
            return False
        return True

    async def insert_wh(self, log: Dict[str, Any]):
        """Insert webhook log with connection retry"""
        try:
            if not await self._ensure_connection():
                print("[ERROR] Failed to insert webhook log: No database connection")
                return False
                
            # Convert time field to int if exists
            if 'entry' in log and isinstance(log['entry'], list):
                for entry in log['entry']:
                    if 'time' in entry and isinstance(entry['time'], (int, float)):
                        entry['time'] = int(entry['time'])
                        
            result = await self.async_logs_collection.insert_one(log)
            return result.inserted_id is not None
            
        except Exception as e:
            print(f"[ERROR] Failed to insert webhook log: {str(e)}")
            return False

    async def get_page_document(self, page_id: str) -> Dict[str, Any]:
        """Get page document by page_id"""
        try:
            if not await self._ensure_connection():
                print("[ERROR] Failed to get page document: No database connection")
                return None
                
            document = await self.async_pages_collection.find_one({"page_id": page_id})
            return document
            
        except Exception as e:
            print(f"[ERROR] Failed to get page document: {str(e)}")
            return None

    async def update_page(self, page_id: str, data: Dict[str, Any]):
        """Update page document"""
        try:
            if not await self._ensure_connection():
                print("[ERROR] Failed to update page: No database connection")
                return False
                
            result = await self.async_pages_collection.update_one(
                {"page_id": page_id},
                {"$set": data},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
            
        except Exception as e:
            print(f"[ERROR] Failed to update page: {str(e)}")
            return False

    def close(self):
        """Close database connections"""
        try:
            if self.client:
                self.client.close()
            if self.async_client:
                self.async_client.close()
            print("[INFO] Database connections closed")
        except Exception as e:
            print(f"[ERROR] Error closing database connections: {str(e)}")

# Create global database instance
db = Database() 