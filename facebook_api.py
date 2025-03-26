import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def send_message(page_id: str, page_access_token: str, recipient_id: str, message_text: str = "hello world"):
    """Send message to Facebook user"""
    url = f"https://graph.facebook.com/v18.0/{page_id}/messages"
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE"
    }
    
    params = {
        "access_token": page_access_token
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, params=params)
            print(f"Message sent to {recipient_id}. Response: {response.text}")
            if response.status_code != 200:
                print(f"Failed to send message. Status code: {response.status_code}")
                print(f"Response: {response.text}")
            return response.status_code == 200
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False

async def reply_to_comment(comment_id: str, page_access_token: str, message: str = "hello world"):
    """Reply to a Facebook comment"""
    url = f"https://graph.facebook.com/v18.0/{comment_id}/comments"
    
    payload = {
        "message": message
    }
    
    params = {
        "access_token": page_access_token
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, params=params)
            print(f"Reply sent to comment {comment_id}. Response: {response.text}")
            if response.status_code != 200:
                print(f"Failed to send reply. Status code: {response.status_code}")
                print(f"Response: {response.text}")
            return response.status_code == 200
    except Exception as e:
        print(f"Error sending reply: {str(e)}")
        return False 