"""
Webhook Forwarder Module - Enterprise version for high-volume data
"""
import httpx
import asyncio
import json
from utils.config import Config
from utils.retry_manager import retry_manager
from utils.facebook_response import reply_to_facebook_comment

async def forward_to_backend(data: dict):
    """
    Forward webhook data to backend with retry mechanism and reply to comment
    
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
                
                # Extract comment info from webhook data
                comment_info = None
                if 'entry' in data:
                    for entry in data['entry']:
                        if 'changes' in entry:
                            for change in entry['changes']:
                                if change.get('value', {}).get('item') == 'comment':
                                    comment_info = {
                                        'comment_id': change['value'].get('comment_id'),
                                        'post_id': change['value'].get('post_id')
                                    }
                                    break
                
                # If this is a comment and backend returned a message, reply to the comment
                if comment_info and response.headers.get('content-type') == 'application/json':
                    response_data = response.json()
                    if 'message' in response_data:
                        await reply_to_facebook_comment(
                            comment_info=comment_info,
                            message=response_data['message'],
                            page_access_token=Config.PAGE_ACCESS_TOKEN
                        )
                    else: print("[INFO] BOT DETECTED")
                
                return True
            else:
                print(f"[WARNING] Backend request failed with status {response.status_code}")
                print(f"[WARNING] Response: {response.text}")
                # Add to retry queue
                # await retry_manager.add_to_retry(data)
                return False
                
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as e:
        print(f"[ERROR] Network error: {str(e)}")
        # Add to retry queue
        # await retry_manager.add_to_retry(data)
        return False
                
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        import traceback
        print(f"Error forwarding to backend:")
        print(f"{str(e)}")
        print(f"Traceback (most recent last):")
        print(traceback.format_exc())
        # Add to retry queue
        # await retry_manager.add_to_retry(data)
        return False 