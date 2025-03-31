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
                print(f"[ERROR] MongoDB connection not available after retries")
                return f"error_no_connection_{time.time()}"
            
            # Check if this is a notification_messages event
            if log.get('event_type') == 'notification_messages':
                if self.async_notification_collection is None:
                    print(f"[ERROR] Notification collection not available")
                    return f"error_no_collection_{time.time()}"
                    
                print(f"[DEBUG] Attempting to insert notification_messages into notification collection")
                result = await self.async_notification_collection.insert_one(log)
                print(f"[INFO] Notification logged successfully with ID: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                if self.async_logs_collection is None:
                    print(f"[ERROR] Logs collection not available")
                    return f"error_no_collection_{time.time()}"
                    
                print(f"[DEBUG] Attempting to insert document into logs collection")
                result = await self.async_logs_collection.insert_one(log)
                print(f"[INFO] Logged successfully with ID: {result.inserted_id}")
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"[ERROR] Error inserting log: {str(e)}")
            print(f"[DEBUG] Log content that failed to insert: {json.dumps(log)[:200]}...")
            return f"error_{time.time()}"

    async def get_page_document(self, page_id: str) -> Dict[str, Any]:
        """Get page document with connection retry"""
        try:
            if not await self._ensure_connection():
                print(f"[ERROR] MongoDB connection not available after retries")
                return {
                    'page_id': page_id,
                    'status': 'off',
                    'page_access_token': '',
                    'store_id': ''
                }
                
            page = await self.async_pages_collection.find_one({"page_id": page_id})
            if page:
                return page
            return {
                'page_id': page_id,
                'status': 'off',
                'page_access_token': '',
                'store_id': ''
            }
        except Exception as e:
            print(f"[ERROR] Error getting page document: {str(e)}")
            return {
                'page_id': page_id,
                'status': 'off',
                'page_access_token': '',
                'store_id': ''
            }

    async def update_page(self, page_id: str, data: Dict[str, Any]):
        """Update page document with connection retry"""
        try:
            if not await self._ensure_connection():
                print(f"[ERROR] MongoDB connection not available after retries")
                return
                
            data['page_id'] = page_id
            await self.async_pages_collection.update_one(
                {"page_id": page_id},
                {"$set": data},
                upsert=True
            )
            print(f"[INFO] Updated page {page_id} successfully")
        except Exception as e:
            print(f"[ERROR] Error updating page: {str(e)}")

    def close(self):
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
            if self.async_client:
                self.async_client.close()
            print(f"[INFO] MongoDB connections closed")
        except Exception as e:
            print(f"[ERROR] Error closing MongoDB connections: {str(e)}")

    async def init_default_page(self):
        """Initialize default page in MongoDB with connection retry"""
        try:
            if not await self._ensure_connection():
                print(f"[ERROR] MongoDB connection not available after retries")
                return
                
            default_page = {
                'page_id': Config.PAGE_ID,
                'status': 'on',
                'page_access_token': Config.PAGE_ACCESS_TOKEN,
                'store_id': 'default_store'
            }
            
            await self.async_pages_collection.update_one(
                {'page_id': default_page['page_id']},
                {'$set': default_page},
                upsert=True
            )
            print("[INFO] Default page initialized successfully with new token")
        except Exception as e:
            print(f"[ERROR] Error initializing default page: {str(e)}")

# Create global database instance
db = Database() 