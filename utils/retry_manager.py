"""
Retry Manager Module
This module manages retry requests with simple retry mechanism
"""
import httpx
import asyncio
from typing import Dict
from datetime import datetime
from utils.config import Config

class RetryManager:
    def __init__(self):
        self.max_retries = 3
        self.timeout = 10.0  # Timeout for each request
        
    async def add_to_retry(self, data: dict) -> bool:
        """
        Retry sending data to backend up to 3 times
        
        Args:
            data (dict): The data to retry sending
            
        Returns:
            bool: True if successful, False if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                print(f"[INFO] Retrying request (attempt {attempt + 1}/{self.max_retries})")
                success = await self.forward_data(data)
                
                if success:
                    print(f"[INFO] Retry successful on attempt {attempt + 1}")
                    return True
                else:
                    print(f"[WARNING] Retry failed on attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:  # Only continue if not last attempt
                        continue
                    else:
                        print(f"[WARNING] All {self.max_retries} retry attempts failed")
                        return False
                    
            except Exception as e:
                print(f"[ERROR] Retry error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:  # Only continue if not last attempt
                    continue
                else:
                    print(f"[WARNING] All {self.max_retries} retry attempts failed")
                    return False
                
        return False
        
    async def forward_data(self, data: dict) -> bool:
        """Forward data to backend directly"""
        try:
            async with httpx.AsyncClient() as client:
                print(f"[INFO] Retrying to backend: {Config.BACKEND_SERVER_URL}")
                print(f"[DEBUG] Retry payload: {data}")
                
                response = await client.post(
                    Config.BACKEND_SERVER_URL,
                    json=data,
                    headers={
                        "Content-Type": "application/json",
                        "api_key": Config.API_KEY
                    },
                    timeout=self.timeout
                )
                
                # Check response
                if response.status_code in [200, 201, 202, 204]:
                    print(f"[INFO] Backend received retry event successfully\n")
                    return True
                else:
                    print(f"[WARNING] Retry failed with status {response.status_code}")
                    print(f"[WARNING] Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Retry error: {str(e)}")
            return False
        
# Create global instance
retry_manager = RetryManager() 