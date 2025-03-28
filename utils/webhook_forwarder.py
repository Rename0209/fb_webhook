"""
Webhook Forwarder Module - Enterprise version for high-volume data
"""
import httpx
import asyncio
import json
from utils.config import Config

async def forward_to_backend(document_id: str, event_type: str, data: dict):
    """
    Forward webhook data to backend
    
    Args:
        document_id (str): The ID of the webhook document
        event_type (str): The type of event
        data (dict): The event data
    """
    try:
        # Extract essential metadata
        essential_metadata = extract_essential_metadata(event_type, data)
        
        # Prepare payload
        payload = {
            "document_id": document_id,
            "event_type": event_type,
            "data": data,
            "metadata": essential_metadata
        }
        
        # Forward to backend
        async with httpx.AsyncClient() as client:
            print(f"[INFO] Forwarding to backend: {Config.BACKEND_SERVER_URL}")
            print(f"[DEBUG] Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                Config.BACKEND_SERVER_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            # Check response
            if response.status_code == 200:
                response_text = response.text.strip()
                if response_text == 'EVENT_RECEIVED':
                    print(f"[INFO] Backend received event successfully")
                    return True
                else:
                    print(f"[WARNING] Unexpected response from backend: {response_text}")
                    return False
            else:
                print(f"[ERROR] Backend request failed with status {response.status_code}")
                print(f"[ERROR] Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"[ERROR] Error forwarding to backend: {str(e)}")
        import traceback
        print(f"Error forwarding to backend:")
        print(f"{str(e)}")
        print(f"Traceback (most recent call last):")
        print(traceback.format_exc())
        return False

def extract_essential_metadata(event_type: str, data: dict) -> dict:
    """
    Extract only essential metadata based on event type
    """
    metadata = {"source": "facebook_webhook"}
    
    if event_type == "message":
        # Trích xuất thông tin tin nhắn
        if "sender_id" in data:
            metadata["sender_id"] = data["sender_id"]
        if "text" in data and isinstance(data["text"], str):
            # Chỉ lấy 50 ký tự đầu của tin nhắn để nhận diện
            metadata["message_preview"] = data["text"][:50]
        if "timestamp" in data:
            metadata["original_timestamp"] = data["timestamp"]
            
    elif event_type == "comment":
        # Trích xuất thông tin bình luận
        if "sender_id" in data:
            metadata["sender_id"] = data["sender_id"]
        if "post_id" in data:
            metadata["post_id"] = data["post_id"]
        if "comment_id" in data:
            metadata["comment_id"] = data["comment_id"]
            
    elif event_type == "reaction" or event_type == "like":
        # Trích xuất thông tin cảm xúc/like
        if "sender_id" in data:
            metadata["sender_id"] = data["sender_id"]
        if "post_id" in data:
            metadata["post_id"] = data["post_id"]
        if "reaction_type" in data:
            metadata["reaction_type"] = data["reaction_type"]
            
    elif event_type == "post_creation":
        # Trích xuất thông tin bài viết mới
        if "sender_id" in data:
            metadata["sender_id"] = data["sender_id"]
        if "post_id" in data:
            metadata["post_id"] = data["post_id"]
        if "message" in data and isinstance(data["message"], str):
            # Chỉ lấy 50 ký tự đầu của bài viết để nhận diện
            metadata["post_preview"] = data["message"][:50]
        if "created_time" in data:
            metadata["created_time"] = data["created_time"]
        if "type" in data:
            metadata["post_type"] = data["type"]
            
    elif event_type == "photo_post":
        # Trích xuất thông tin bài viết có ảnh
        if "sender_id" in data:
            metadata["sender_id"] = data["sender_id"]
        if "post_id" in data:
            metadata["post_id"] = data["post_id"]
        if "message" in data and isinstance(data["message"], str):
            # Chỉ lấy 50 ký tự đầu của bài viết để nhận diện
            metadata["post_preview"] = data["message"][:50]
        if "created_time" in data:
            metadata["created_time"] = data["created_time"]
        if "photo_id" in data:
            metadata["photo_id"] = data["photo_id"]
        # Thêm flag để biết đây là bài viết có ảnh
        metadata["has_photo"] = True
    
    # Thêm trường tổng quát để biết metadata đã được trích xuất
    metadata["is_metadata_only"] = True
    metadata["full_data_available_in_db"] = True
    
    return metadata

def should_process_async(event_type: str, data: dict) -> bool:
    """
    Quyết định xem sự kiện có nên được xử lý bất đồng bộ không
    """
    # Cho mục đích test, hãy chọn xử lý bất đồng bộ cho sự kiện comment, post_creation và photo_post
    if event_type in ["comment", "post_creation", "photo_post"]:
        return True
        
    # Ví dụ về logic quyết định
    high_priority_events = ["order_created", "payment_received"]
    large_data_threshold = 10000  # bytes
    
    if event_type in high_priority_events:
        return True
        
    # Kiểm tra kích thước dữ liệu
    data_size = len(json.dumps(data))
    if data_size > large_data_threshold:
        return True
        
    return False  # Mặc định xử lý đồng bộ

async def log_failed_forward(document_id, event_type, metadata, status_code, error_msg=None):
    """Log failed forwarding for retry processing"""
    # This would typically write to a retry queue or separate collection
    print(f"Logging failed forward for retry: {document_id}")
    # In a real implementation, you would save this to a retry queue or database
    # For example:
    # await db.retry_queue.insert_one({
    #     "document_id": document_id,
    #     "event_type": event_type,
    #     "metadata": metadata,
    #     "status_code": status_code,
    #     "error": error_msg,
    #     "retry_count": 0,
    #     "created_at": datetime.now()
    # }) 