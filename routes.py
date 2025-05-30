"""
Routes Module
This module defines the API routes and handlers.
"""
import time
import json
import hmac
import hashlib
from fastapi import Request, Response, APIRouter, BackgroundTasks
from utils.error_handler import log_error
from utils.webhook_forwarder import forward_to_backend
from utils.config import Config
from database import db

# Create router
router = APIRouter()

async def verify_facebook_signature(request: Request) -> bool:
    """
    Verify that the webhook request came from Facebook using signed signature.
    """
    # Get signature from header
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        print("[ERROR] No signature found in headers")
        print("[DEBUG] Available headers:", request.headers)
        return False
    
    # Get raw body
    body = await request.body()
    
    # Get app secret from config
    app_secret = Config.FACEBOOK_APP_SECRET
    if not app_secret:
        print("[ERROR] No app secret configured")
        return False
        
    # Calculate expected signature
    expected_signature = hmac.new(
        app_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    actual_signature = signature.split('=')[1]
    
    # Debug information
    print("[DEBUG] Signature validation details:")
    print(f"[DEBUG] - Received signature: {actual_signature}")
    print(f"[DEBUG] - Calculated signature: {expected_signature}")
    print(f"[DEBUG] - Body length: {len(body)} bytes")
    print(f"[DEBUG] - Body preview: {body[:100]}...")
    
    if not hmac.compare_digest(actual_signature, expected_signature):
        print("[ERROR] Signature verification failed")
        print("[DEBUG] - Signatures do not match")
        return False
        
    print("[INFO] Signature verification successful")
    return True

async def process_webhook_data(raw_data: dict, time_id: float):
    """
    Process webhook data in background
    
    Args:
        raw_data (dict): The raw webhook data
        time_id (float): Timestamp of the webhook
    """
    try:
        # Create a copy of raw data for forwarding
        data_to_forward = raw_data.copy()
        
        # Save to database first
        # await db.insert_wh(raw_data)
        
        # Forward to backend if enabled and it's a comment
        if Config.ENABLE_FORWARDING:
            # Check if it's a comment from Facebook
            is_comment = False
            if 'entry' in raw_data:
                for entry in raw_data['entry']:
                    if 'changes' in entry:
                        for change in entry['changes']:
                            if change.get('value', {}).get('item') == 'comment':
                                is_comment = True
                                break
                    if is_comment:
                        break
            
            if is_comment:
                print(f"[INFO] Forwarding comment event to backend")
                try:
                    # Forward the copy of raw data
                    await forward_to_backend(data=data_to_forward)
                    
                except Exception as e:
                    print(f"[ERROR] Failed to forward to backend: {str(e)}")
                    # Create error log for failed forward
                    error_log = {
                        'type': 'fb_event_forward_error',
                        'time_id': time_id,
                        'error': str(e),
                        'status': 'pending_retry'
                    }
                    await db.insert_wh(error_log)
            else:
                print(f"[INFO] Skipping forward - not a comment event")
    
    except Exception as e:
        print(f"[ERROR] Webhook processing error: {str(e)}")
        await log_error(db, e, time_id)

@router.get("/qawh")
@router.get("/fqawh")
async def verify(request: Request):
    """
    Webhook verification endpoint
    
    On webhook verification, VERIFY_TOKEN has to match the token at the
    configuration and send back "hub.challenge" as success.
    """
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get(
        "hub.challenge"
    ):
        if (
            not request.query_params.get("hub.verify_token")
            == Config.VERIFY_TOKEN
        ):
            return Response(content="Verification token mismatch", status_code=403)
        return Response(content=request.query_params["hub.challenge"])

    return Response(content="Required arguments haven't passed.", status_code=400)

@router.post("/qawh")
@router.post("/fqawh")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook handler for Facebook events
    
    This endpoint receives webhook events from Facebook and processes them.
    Returns response immediately to prevent Facebook from resending.
    """
    time_id = time.time()
    
    try:
        # Verify Facebook signature
        if not await verify_facebook_signature(request):
            return Response(
                content=json.dumps({
                    "status": "error",
                    "message": "Invalid signature"
                }),
                status_code=403,
                media_type="application/json"
            )
            
        # Parse raw body as JSON
        raw_data = await request.json()
        
        if raw_data.get("object") == "page":
            # Add webhook processing to background tasks
            background_tasks.add_task(process_webhook_data, raw_data, time_id)
            
            # Return response immediately
            return Response(
                content=json.dumps({
                    "status": "success",
                    "message": "Webhook received",
                    "time_id": time_id
                }),
                status_code=200,
                media_type="application/json"
            )
            
        return Response(
            content=json.dumps({"status": "success", "message": "not_a_page_event"}),
            status_code=200,
            media_type="application/json"
        )
        
    except Exception as e:
        print(f"[ERROR] Webhook processing error: {str(e)}")
        await log_error(db, e, time_id)
        
        return Response(
            content=json.dumps({
                "status": "error",
                "message": str(e),
                "time_id": time_id
            }),
            status_code=200,
            media_type="application/json"
        ) 