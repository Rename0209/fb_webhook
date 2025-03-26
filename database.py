from typing import Dict, Any
import time
from pymongo import MongoClient
from utils.config import Config

class Database:
    def __init__(self):
        # MongoDB connection
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DB]
        self.logs_collection = self.db[Config.MONGODB_COLLECTION_LOGS]
        self.pages_collection = self.db[Config.MONGODB_COLLECTION_PAGES]
        
        # Create indexes
        self.logs_collection.create_index("time_id")
        self.pages_collection.create_index("page_id", unique=True)

    async def insert_wh(self, log: Dict[str, Any]):
        """Insert webhook log"""
        try:
            result = self.logs_collection.insert_one(log)
            print(f"Logged successfully with ID: {result.inserted_id}")
            return str(result.inserted_id)  # Convert ObjectId to string
        except Exception as e:
            print(f"Error inserting log: {str(e)}")
            return None

    async def get_page_document(self, page_id: str) -> Dict[str, Any]:
        """Get page document"""
        try:
            page = self.pages_collection.find_one({"page_id": page_id})
            if page:
                return page
            return {
                'page_id': page_id,
                'status': 'off',
                'page_access_token': '',
                'store_id': ''
            }
        except Exception as e:
            print(f"Error getting page document: {str(e)}")
            return {
                'page_id': page_id,
                'status': 'off',
                'page_access_token': '',
                'store_id': ''
            }

    async def update_page(self, page_id: str, data: Dict[str, Any]):
        """Update page document"""
        try:
            data['page_id'] = page_id
            self.pages_collection.update_one(
                {"page_id": page_id},
                {"$set": data},
                upsert=True
            )
            print(f"Updated page {page_id} successfully")
        except Exception as e:
            print(f"Error updating page: {str(e)}")

    def close(self):
        """Close MongoDB connection"""
        self.client.close()

    def init_default_page(self):
        """Initialize default page in MongoDB"""
        try:
            default_page = {
                'page_id': Config.PAGE_ID,
                'status': 'on',
                'page_access_token': Config.PAGE_ACCESS_TOKEN,
                'store_id': 'default_store'
            }
            
            # Insert or update the default page
            self.pages_collection.update_one(
                {'page_id': default_page['page_id']},
                {'$set': default_page},
                upsert=True
            )
            print("Default page initialized successfully with new token")
        except Exception as e:
            print(f"Error initializing default page: {str(e)}")

# Create global database instance
db = Database() 