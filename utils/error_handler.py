"""
Error Handler Module
This module handles error logging and exception management.
"""
import traceback
import time

async def log_error(db, error, time_id=None):
    """
    Log error to database
    
    Args:
        db: Database instance
        error: Exception or error message
        time_id: Timestamp of the error (optional)
    
    Returns:
        None
    """
    if time_id is None:
        time_id = time.time()
        
    print('Error processing webhook:')
    print(str(error))
    print(traceback.format_exc())
    print('force confirm')
    
    error_log = {
        'type': 'fb_event_force_confirm', 
        'message': {'text': traceback.format_exc()}, 
        'time_id': time_id
    }
    
    await db.insert_wh(error_log) 