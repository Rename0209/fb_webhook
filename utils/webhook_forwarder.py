"""
Webhook Forwarder Module - Enterprise version for high-volume data
"""
import httpx
import asyncio
import json
from utils.config import Config
from utils.retry_manager import retry_manager

async def forward_to_backend(data: dict):
    """
    Forward webhook data to backend with retry mechanism
    
    Args:
        data (dict): The raw webhook data
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Forward to backend
        async with httpx.AsyncClient() as client:
            print(f"[INFO] Forwarding to backend: {Config.BACKEND_SERVER_URL}")
            print(f"[DEBUG] Payload: {json.dumps(data, indent=2)}")
            
            response = await client.post(
                Config.BACKEND_SERVER_URL,
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "api_key": Config.API_KEY
                },
                timeout=15.0
            )
            
            # Check response
            if response.status_code in [200, 201, 202, 204]:  # Any of these status codes are considered successful
                print(f"[INFO] Backend received event successfully")
                return True
            else:
                print(f"[WARNING] Backend request failed with status {response.status_code}")
                print(f"[WARNING] Response: {response.text}")
                # Add to retry queue
                await retry_manager.add_to_retry(data)
                return False
                
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as e:
        print(f"[ERROR] Network error: {str(e)}")
        # Add to retry queue
        await retry_manager.add_to_retry(data)
        return False
                
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        import traceback
        print(f"Error forwarding to backend:")
        print(f"{str(e)}")
        print(f"Traceback (most recent last):")
        print(traceback.format_exc())
        # Add to retry queue
        await retry_manager.add_to_retry(data)
        return False 