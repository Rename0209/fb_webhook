"""
Facebook Webhook Parser Module
This module handles parsing and extracting structured data from Facebook webhook events.
"""
import time
import json
from enum import Enum, auto

class FacebookEventType(Enum):
    """Enum class for Facebook webhook event types"""
    MESSAGE = auto()
    COMMENT = auto()
    REACTION = auto()
    LIKE = auto()
    POST_CREATION = auto()
    PHOTO_POST = auto()
    NOTIFICATION_MESSAGES = auto()
    ADDRESS_FORM = auto()
    UNKNOWN = auto()

    @classmethod
    def from_string(cls, event_type: str) -> 'FacebookEventType':
        """Convert string event type to enum"""
        event_type_map = {
            'message': cls.MESSAGE,
            'comment': cls.COMMENT,
            'reaction': cls.REACTION,
            'like': cls.LIKE,
            'post_creation': cls.POST_CREATION,
            'photo_post': cls.PHOTO_POST,
            'notification_messages': cls.NOTIFICATION_MESSAGES,
            'address_form': cls.ADDRESS_FORM
        }
        return event_type_map.get(event_type, cls.UNKNOWN)

def extract_structured_data(raw_data):
    """
    Extract and structure data from the raw Facebook webhook payload
    
    Args:
        raw_data (dict): The raw webhook data from Facebook
        
    Returns:
        dict: Structured data containing event information, or None if event should be skipped
    """
    time_id = time.time()
    event_type = "unknown"
    structured_data = {
        'time_id': time_id,
        'version_api': '21-03: 17.00',
        'type': 'fb_event_in',
        'page_id': None,
        'event_type': event_type,
        'data': {}
    }
    
    # Process entries
    for entry in raw_data.get("entry", []):
        # Set page ID
        page_id = entry.get("id")
        structured_data['page_id'] = page_id
        
        # Check for messaging (private messages)
        if "messaging" in entry:
            result = _parse_messaging_event(entry, structured_data)
            if result:
                return result
        
        # Check for changes (comments, reactions, etc.)
        if "changes" in entry:
            result = _parse_changes_event(entry, structured_data)
            if result:
                return result
            # If result is None, it means we should skip this event (e.g., comment from page)
            return None
    
    # Return the structured data
    return structured_data

def _parse_messaging_event(entry, structured_data):
    """
    Parse messaging events (private messages)
    
    Args:
        entry (dict): The entry containing messaging events
        structured_data (dict): Base structured data object
        
    Returns:
        dict: Updated structured data or None if no valid events
    """
    for messaging in entry.get("messaging", []):
        # Check for optin event (notification_messages)
        if "optin" in messaging:
            return EventHandler.handle_notification_messages(messaging, structured_data)
            
        # Check for address form event
        if "messaging_customer_information" in messaging:
            return EventHandler.handle_address_form(messaging, structured_data)
        
        # Handle regular messages
        return EventHandler.handle_message(messaging, structured_data)
    
    return None

def _parse_changes_event(entry, structured_data):
    """
    Parse changes events (comments, reactions, etc.)
    
    Args:
        entry (dict): The entry containing changes events
        structured_data (dict): Base structured data object
        
    Returns:
        dict: Updated structured data or None if event should be skipped
    """
    for change in entry.get("changes", []):
        value = change.get("value", {})
        field = change.get("field", "")
        
        if field == "feed":
            item = value.get("item")
            verb = value.get("verb")
            
            if item == "comment":
                result = EventHandler.handle_comment(value, structured_data)
                if result is None:
                    print("Skipping comment event: Comment is from page")
                    return None
                return result
            elif item == "reaction":
                return EventHandler.handle_reaction(value, structured_data)
            elif item == "like":
                return EventHandler.handle_like(value, structured_data)
            elif item == "status" and verb == "add":
                return EventHandler.handle_post_creation(value, structured_data)
            elif item == "photo" and verb == "add":
                return EventHandler.handle_photo_post(value, structured_data)
    
    return None

class EventHandler:
    """Class to handle different types of Facebook events"""
    
    @staticmethod
    def handle_message(messaging: dict, structured_data: dict) -> dict:
        """Handle message events"""
        event_type = "message"
        sender_id = messaging.get("sender", {}).get("id")
        recipient_id = messaging.get("recipient", {}).get("id")
        message = messaging.get("message", {})
        
        structured_data['event_type'] = event_type
        structured_data['data'] = {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message_id": message.get("mid"),
            "text": message.get("text"),
            "timestamp": messaging.get("timestamp")
        }
        
        print(f"Received message from {sender_id}: {json.dumps(message)}")
        return structured_data

    @staticmethod
    def handle_notification_messages(messaging: dict, structured_data: dict) -> dict:
        """Handle notification messages events"""
        optin = messaging.get("optin", {})
        
        if optin.get("type") != "notification_messages":
            return None
            
        token = optin.get("notification_messages_token")
        current_status = optin.get("notification_messages_status")
        new_status = "AVAILABLE" if not current_status or current_status == "RESUME_NOTIFICATIONS" else "NOT_AVAILABLE"
        
        notification_data = {
            "sender_id": messaging.get("sender", {}).get("id"),
            "recipient_id": messaging.get("recipient", {}).get("id"),
            "notification_messages_token": token,
            "token_expiry_timestamp": optin.get("token_expiry_timestamp"),
            "user_token_status": optin.get("user_token_status"),
            "notification_messages_timezone": optin.get("notification_messages_timezone"),
            "title": optin.get("title"),
            "notification_messages_status": new_status
        }
        
        structured_data['event_type'] = "notification_messages"
        structured_data['data'] = notification_data
        
        print(f"Received notification_messages event: {json.dumps(notification_data)}")
        return structured_data

    @staticmethod
    def handle_address_form(messaging: dict, structured_data: dict) -> dict:
        """Handle address form events"""
        event_type = "address_form"
        sender_id = messaging.get("sender", {}).get("id")
        recipient_id = messaging.get("recipient", {}).get("id")
        customer_info = messaging.get("messaging_customer_information", {})
        
        # Extract address information from screens
        address_data = {}
        for screen in customer_info.get("screens", []):
            if screen.get("screen_id") == "Add address":
                for response in screen.get("responses", []):
                    key = response.get("key")
                    value = response.get("value")
                    if key and value:
                        address_data[key] = value
        
        # Prepare the data structure
        form_data = {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "timestamp": messaging.get("timestamp"),
            "address": address_data
        }
        
        structured_data['event_type'] = event_type
        structured_data['data'] = form_data
        
        print(f"SUCCESS: Address form processed from user {sender_id}")
        return structured_data

    @staticmethod
    def handle_comment(value: dict, structured_data: dict) -> dict:
        """Handle comment events"""
        sender = value.get("from", {})
        sender_id = sender.get("id")
        sender_name = sender.get("name")
        page_id = structured_data.get('page_id')
        
        if sender_id == page_id:
            print(f"SKIPPING: Comment is from page itself")
            return None
            
        comment_data = {
            "sender_id": sender_id,
            "sender_name": sender_name,
            "post_id": value.get("post_id"),
            "comment_id": value.get("comment_id"),
            "message": value.get("message"),
            "created_time": value.get("created_time"),
            "parent_id": value.get("parent_id"),
            "is_hidden": value.get("is_hidden", False),
            "is_private": value.get("is_private", False)
        }
        
        structured_data['event_type'] = "comment"
        structured_data['data'] = comment_data
        
        print(f"SUCCESS: Comment processed from user {sender_name} (ID: {sender_id})")
        return structured_data

    @staticmethod
    def handle_reaction(value: dict, structured_data: dict) -> dict:
        """Handle reaction events"""
        event_type = "reaction"
        reaction_type = value.get("reaction_type")
        post_id = value.get("post_id")
        sender_id = value.get("from", {}).get("id")
        sender_name = value.get("from", {}).get("name")
        
        post_parts = post_id.split("_") if post_id else ["", ""]
        page_id = post_parts[0]
        post_number = post_parts[1] if len(post_parts) > 1 else ""
        
        reaction_data = {
            "sender_id": sender_id,
            "sender_name": sender_name,
            "post_id": post_id,
            "reaction_type": reaction_type,
            "created_time": value.get("created_time"),
            "page_id": page_id,
            "post_number": post_number
        }
        
        structured_data['event_type'] = event_type
        structured_data['data'] = reaction_data
        
        print(f"SUCCESS: Reaction processed from user {sender_name} (ID: {sender_id})")
        return structured_data

    @staticmethod
    def handle_like(value: dict, structured_data: dict) -> dict:
        """Handle like events"""
        event_type = "like"
        post_id = value.get("post_id")
        sender_id = value.get("from", {}).get("id")
        sender_name = value.get("from", {}).get("name")
        
        post_parts = post_id.split("_") if post_id else ["", ""]
        page_id = post_parts[0]
        post_number = post_parts[1] if len(post_parts) > 1 else ""
        
        like_data = {
            "sender_id": sender_id,
            "sender_name": sender_name,
            "post_id": post_id,
            "created_time": value.get("created_time"),
            "page_id": page_id,
            "post_number": post_number
        }
        
        structured_data['event_type'] = event_type
        structured_data['data'] = like_data
        
        print(f"SUCCESS: Like processed from user {sender_name} (ID: {sender_id})")
        return structured_data

    @staticmethod
    def handle_post_creation(value: dict, structured_data: dict) -> dict:
        """Handle post creation events"""
        event_type = "post_creation"
        post_id = value.get("post_id")
        sender_id = value.get("from", {}).get("id")
        sender_name = value.get("from", {}).get("name")
        
        post_data = {
            "sender_id": sender_id,
            "sender_name": sender_name,
            "post_id": post_id,
            "message": value.get("message"),
            "created_time": value.get("created_time"),
            "type": value.get("type", "status")
        }
        
        structured_data['event_type'] = event_type
        structured_data['data'] = post_data
        
        print(f"SUCCESS: Post creation processed from user {sender_name} (ID: {sender_id})")
        return structured_data

    @staticmethod
    def handle_photo_post(value: dict, structured_data: dict) -> dict:
        """Handle photo post events"""
        event_type = "photo_post"
        post_id = value.get("post_id")
        sender_id = value.get("from", {}).get("id")
        sender_name = value.get("from", {}).get("name")
        
        photo_data = {
            "sender_id": sender_id,
            "sender_name": sender_name,
            "post_id": post_id,
            "message": value.get("message"),
            "created_time": value.get("created_time"),
            "photo_id": value.get("photo_id"),
            "type": "photo"
        }
        
        structured_data['event_type'] = event_type
        structured_data['data'] = photo_data
        
        print(f"SUCCESS: Photo post processed from user {sender_name} (ID: {sender_id})")
        return structured_data 