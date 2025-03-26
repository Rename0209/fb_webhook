"""
Routes Module
This module defines the API routes and handlers.
"""
import time
import json
from fastapi import Request, Response, APIRouter, BackgroundTasks
from utils.webhook_parser import extract_structured_data
from utils.error_handler import log_error
from utils.webhook_forwarder import forward_to_backend
from utils.config import Config
from database import db

# Create router
router = APIRouter()

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
    Returns response immediately and processes data in background.
    """
    time_id = time.time()
    
    try:
        # Parse raw body as JSON
        raw_data = await request.json()
        
        if raw_data.get("object") == "page":
            # Extract and process data
            structured_data = extract_structured_data(raw_data)
            
            # Skip processing if structured_data is None (e.g., comment from page)
            if structured_data is None:
                print(f"[SKIP] Comment from page itself")
                return Response(
                    content=json.dumps({
                        "status": "skipped",
                        "reason": "event_should_be_skipped",
                        "message": "Event was skipped (e.g., comment from page)"
                    }),
                    status_code=200,
                    media_type="application/json"
                )
            
            event_type = structured_data.get('event_type')
            event_data = structured_data.get('data', {})
            
            # Return response immediately
            response_data = {
                "status": "success",
                "message": "Webhook received, processing in background",
                "event_type": event_type,
                "time_id": time_id
            }
            
            # Add processing task to background tasks
            background_tasks.add_task(
                process_webhook_data,
                structured_data=structured_data,
                time_id=time_id,
                event_type=event_type,
                event_data=event_data
            )
            
            return Response(
                content=json.dumps(response_data),
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

async def process_webhook_data(structured_data: dict, time_id: float, event_type: str, event_data: dict):
    """
    Process webhook data in background
    
    Args:
        structured_data (dict): The structured webhook data
        time_id (float): The time ID of the webhook
        event_type (str): The type of event
        event_data (dict): The event data
    """
    try:
        # Save the structured data and get the document ID
        document_id = await db.insert_wh(structured_data)
        
        # Create confirmation log
        confirm_log = {
            'type': 'fb_event_confirm', 
            'time_id': time_id,
            'related_document_id': document_id,
            'event_type': event_type,
            'page_id': structured_data.get('page_id')
        }
        await db.insert_wh(confirm_log)
        
        # Forward to backend if enabled
        if Config.ENABLE_FORWARDING and document_id:
            await forward_to_backend(
                document_id=document_id,
                event_type=event_type,
                data=event_data
            )
        
    except Exception as e:
        print(f"[ERROR] Background processing error: {str(e)}")
        await log_error(db, e, time_id) 