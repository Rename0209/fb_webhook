"""
Facebook Webhook Parser Module
This module handles parsing and extracting structured data from Facebook webhook events.
"""
import time
import json

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
        
        # Identify comment
        if field == "feed" and value.get("item") == "comment":
            result = _parse_comment_event(value, structured_data)
            if result is None:
                print("Skipping comment event: Comment is from page")
                return None
            return result
        
        # Identify reaction
        elif field == "feed" and value.get("item") == "reaction":
            return _parse_reaction_event(value, structured_data)
        
        # Identify like
        elif field == "feed" and value.get("item") == "like":
            return _parse_like_event(value, structured_data)
            
        # Identify post creation
        elif field == "feed" and value.get("item") == "status" and value.get("verb") == "add":
            return _parse_post_creation_event(value, structured_data)
            
        # Identify photo post creation
        elif field == "feed" and value.get("item") == "photo" and value.get("verb") == "add":
            return _parse_photo_post_event(value, structured_data)
    
    return None

def _parse_comment_event(value, structured_data):
    """
    Parse comment event data
    
    Args:
        value (dict): The comment event value
        structured_data (dict): Base structured data object
        
    Returns:
        dict: Updated structured data or None if comment is from page
    """
    # Get sender information
    sender = value.get("from", {})
    sender_id = sender.get("id")
    sender_name = sender.get("name")
    page_id = structured_data.get('page_id')
    
    # Log detailed information about the comment
    print(f"\nProcessing comment event:")
    print(f"Sender ID: {sender_id}")
    print(f"Sender Name: {sender_name}")
    print(f"Page ID: {page_id}")
    
    # Check if comment is from the page itself
    if sender_id == page_id:
        print(f"SKIPPING: Comment is from page itself")
        print(f"Reason: sender_id ({sender_id}) matches page_id ({page_id})")
        return None
        
    # Extract comment data
    comment_data = {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "post_id": value.get("post_id"),
        "comment_id": value.get("comment_id"),
        "message": value.get("message"),
        "created_time": value.get("created_time"),
        "parent_id": value.get("parent_id"),  # For replies to comments
        "is_hidden": value.get("is_hidden", False),
        "is_private": value.get("is_private", False)
    }
    
    # Set event type and data
    structured_data['event_type'] = "comment"
    structured_data['data'] = comment_data
    
    print(f"SUCCESS: Comment processed from user {sender_name} (ID: {sender_id})")
    print(f"Comment details: {json.dumps(comment_data, indent=2)}")
    
    return structured_data

def _parse_reaction_event(value, structured_data):
    """
    Parse reaction events
    
    Args:
        value (dict): The reaction event data
        structured_data (dict): Base structured data object
        
    Returns:
        dict: Updated structured data with reaction information
    """
    event_type = "reaction"
    reaction_type = value.get("reaction_type")
    post_id = value.get("post_id")
    sender_id = value.get("from", {}).get("id")
    sender_name = value.get("from", {}).get("name")
    
    # Extract post information
    post_parts = post_id.split("_") if post_id else ["", ""]
    page_id = post_parts[0]
    post_number = post_parts[1] if len(post_parts) > 1 else ""
    
    # Generate post URL
    post_url = f"https://www.facebook.com/{page_id}/posts/{post_number}" if page_id and post_number else ""
    
    structured_data['event_type'] = event_type
    structured_data['data'] = {
        "reaction_type": reaction_type,
        "post_id": post_id,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "post_url": post_url,
        "created_time": value.get("created_time"),
        "verb": value.get("verb")  # add, edit, remove
    }
    
    print(f"Received reaction {reaction_type} on post {post_id}")
    return structured_data

def _parse_like_event(value, structured_data):
    """
    Parse like events
    
    Args:
        value (dict): The like event data
        structured_data (dict): Base structured data object
        
    Returns:
        dict: Updated structured data with like information
    """
    event_type = "like"
    post_id = value.get("post_id")
    sender_id = value.get("from", {}).get("id")
    sender_name = value.get("from", {}).get("name")
    
    # Extract post information
    post_parts = post_id.split("_") if post_id else ["", ""]
    page_id = post_parts[0]
    post_number = post_parts[1] if len(post_parts) > 1 else ""
    
    # Generate post URL
    post_url = f"https://www.facebook.com/{page_id}/posts/{post_number}" if page_id and post_number else ""
    
    structured_data['event_type'] = event_type
    structured_data['data'] = {
        "post_id": post_id,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "post_url": post_url,
        "created_time": value.get("created_time"),
        "verb": value.get("verb")  # add, remove
    }
    
    print(f"Received like on post {post_id}")
    return structured_data

def _parse_post_creation_event(value, structured_data):
    """
    Parse post creation events
    
    Args:
        value (dict): The post creation event data
        structured_data (dict): Base structured data object
        
    Returns:
        dict: Updated structured data with post creation information
    """
    event_type = "post_creation"
    post_id = value.get("post_id")
    sender_id = value.get("from", {}).get("id")
    sender_name = value.get("from", {}).get("name")
    message = value.get("message", "")
    
    # Extract post information
    post_parts = post_id.split("_") if post_id else ["", ""]
    page_id = post_parts[0]
    post_number = post_parts[1] if len(post_parts) > 1 else ""
    
    # Generate post URL
    post_url = f"https://www.facebook.com/{page_id}/posts/{post_number}" if page_id and post_number else ""
    
    structured_data['event_type'] = event_type
    structured_data['data'] = {
        "post_id": post_id,
        "message": message,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "post_url": post_url,
        "created_time": value.get("created_time"),
        "is_published": value.get("is_published", True),
        "link": value.get("link", ""),
        "type": value.get("type", "status")  # status, link, photo, video, etc.
    }
    
    print(f"Received post creation event: {post_id} - {message[:50]}...")
    return structured_data

def _parse_photo_post_event(value, structured_data):
    """
    Parse photo post events
    
    Args:
        value (dict): The photo post event data
        structured_data (dict): Base structured data object
        
    Returns:
        dict: Updated structured data with photo post information
    """
    event_type = "photo_post"
    post_id = value.get("post_id")
    sender_id = value.get("from", {}).get("id")
    sender_name = value.get("from", {}).get("name")
    message = value.get("message", "")
    
    # Extract post information
    post_parts = post_id.split("_") if post_id else ["", ""]
    page_id = post_parts[0]
    post_number = post_parts[1] if len(post_parts) > 1 else ""
    
    # Generate post URL
    post_url = f"https://www.facebook.com/{page_id}/posts/{post_number}" if page_id and post_number else ""
    
    # Extract photo information
    photo_id = value.get("photo_id", "")
    link = value.get("link", "")
    photo_url = value.get("photo_url", link)  # Use link as fallback for photo_url
    
    structured_data['event_type'] = event_type
    structured_data['data'] = {
        "post_id": post_id,
        "message": message,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "post_url": post_url,
        "created_time": value.get("created_time"),
        "is_published": value.get("is_published", True),
        "link": link,
        "photo_id": photo_id,
        "photo_url": photo_url,
        "type": "photo"
    }
    
    print(f"Received photo post event: {post_id} - {message[:50]}...")
    return structured_data 