"""
Retry Manager Module
This module manages retry requests with priority for new data
"""
import httpx
import asyncio
from typing import Dict, List
from datetime import datetime
from utils.config import Config

class RetryManager:
    def __init__(self):
        self.retry_queue: Dict[str, dict] = {}  # {data_id: retry_data}
        self.max_retries = 3
        self.timeout = 3.0
        self.processing_task = None
        self.max_queue_size = 100  # Maximum number of items in queue
        
    async def add_to_retry(self, data: dict, retry_count: int = 0):
        """Add data to retry queue"""
        # Check if queue is full
        if len(self.retry_queue) >= self.max_queue_size:
            print(f"[WARNING] Retry queue is full (max size: {self.max_queue_size}), dropping request")
            return
            
        data_id = str(datetime.now().timestamp())
        self.retry_queue[data_id] = {
            'data': data,
            'retry_count': retry_count,
            'last_retry_time': datetime.now()
        }
        
        # Only start processing if not already running
        if self.processing_task is None or self.processing_task.done():
            self.processing_task = asyncio.create_task(self.process_retry_queue())
            
    async def process_retry_queue(self):
        """Process retry queue"""
        while self.retry_queue:
            # Get the oldest data first
            data_id = next(iter(self.retry_queue))
            retry_data = self.retry_queue[data_id]
            
            # Check if we should retry
            if retry_data['retry_count'] < self.max_retries:
                try:
                    print(f"[INFO] Retrying request (attempt {retry_data['retry_count'] + 1}/{self.max_retries})")
                    # Forward data directly without using forward_to_backend
                    success = await self.forward_data(retry_data['data'])
                    
                    if success:
                        # Remove from queue if successful
                        del self.retry_queue[data_id]
                    else:
                        # Update retry count and time
                        retry_data['retry_count'] += 1
                        retry_data['last_retry_time'] = datetime.now()
                        
                        # Wait before next retry
                        await asyncio.sleep(self.timeout)
                except Exception as e:
                    print(f"[ERROR] Error processing retry: {str(e)}")
                    retry_data['retry_count'] += 1
                    retry_data['last_retry_time'] = datetime.now()
                    await asyncio.sleep(self.timeout)
            else:
                print(f"[WARNING] Max retries ({self.max_retries}) reached for request")
                # Remove from queue if max retries reached
                del self.retry_queue[data_id]
                
        self.processing_task = None
        
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
                    timeout=3.0
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