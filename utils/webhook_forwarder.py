"""
Webhook Forwarder Module - Enterprise version for high-volume data
"""
import httpx
import asyncio
import json
from utils.config import Config

async def forward_to_backend(document_id: str, event_type: str, data: dict):
    """
    Forward webhook data to backend with smart handling of response codes
    """
    try:
        print(f"\n=== Starting to forward document {document_id} to backend ===")
        print(f"Event type: {event_type}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print(f"Backend URL: {Config.BACKEND_SERVER_URL}")
        print(f"Forwarding enabled: {Config.ENABLE_FORWARDING}")
        
        if not Config.ENABLE_FORWARDING:
            print("Forwarding is disabled in configuration")
            return {
                "success": False,
                "error": "Forwarding is disabled"
            }
        
        # Xác định nếu event này nên được xử lý đồng bộ hay bất đồng bộ
        is_async_event = should_process_async(event_type, data)
        print(f"Processing mode: {'async' if is_async_event else 'sync'}")
        
        # Trích xuất metadata để kiểm tra, ngay cả khi không sử dụng
        metadata = extract_essential_metadata(event_type, data)
        print(f"Extracted metadata: {json.dumps(metadata, indent=2)}")
        
        # Xác định dữ liệu để gửi
        payload_data = metadata if is_async_event else data
        print(f"Payload type: {'metadata only' if is_async_event else 'full data'}")
        print(f"Payload size: {len(json.dumps(payload_data))} characters")
        
        payload = {
            "document_id": document_id,
            "event_type": event_type,
            "data": payload_data,
            "timestamp": asyncio.get_event_loop().time(),
            "processing_preference": "async" if is_async_event else "sync"
        }
        
        print(f"\nSending POST request to: {Config.BACKEND_SERVER_URL}")
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        
        async with httpx.AsyncClient(timeout=Config.FORWARD_TIMEOUT) as client:
            try:
                response = await client.post(Config.BACKEND_SERVER_URL, json=payload)
                print(f"\nResponse status code: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response body: {response.text}")
                
                # Xử lý status code đúng cách
                if response.status_code == 200:
                    print(f"Document {document_id} processed synchronously")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "sync": True,
                        "response": response.json() if response.text else None
                    }
                elif response.status_code in [201, 202]:
                    print(f"Document {document_id} accepted for asynchronous processing")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "sync": False
                    }
                else:
                    print(f"Failed to forward document {document_id}. Status code: {response.status_code}")
                    print(f"Response: {response.text}")
                    # Log the failure for retry processing
                    await log_failed_forward(document_id, event_type, data, response.status_code)
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text
                    }
            except httpx.ConnectError as e:
                print(f"Connection error: {str(e)}")
                return {
                    "success": False,
                    "error": f"Connection error: {str(e)}"
                }
            except httpx.TimeoutException as e:
                print(f"Timeout error: {str(e)}")
                return {
                    "success": False,
                    "error": f"Timeout error: {str(e)}"
                }
                
    except Exception as e:
        print(f"\nError forwarding document {document_id}: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Log the exception for retry processing
        await log_failed_forward(document_id, event_type, data, 0, str(e))
        return {
            "success": False,
            "error": str(e)
        }

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