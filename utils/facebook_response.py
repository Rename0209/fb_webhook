import httpx
import logging
from typing import Optional, Dict, Any

async def reply_to_facebook_comment(comment_info: Dict[str, str], message: str, page_access_token: str) -> Optional[Dict[str, Any]]:
    """
    Reply to a Facebook comment as a Page.

    Args:
        comment_info (Dict[str, str]): Dictionary containing comment_id and post_id
        message (str): The message to send in the reply
        page_access_token (str): A valid Page Access Token

    Returns:
        Optional[Dict[str, Any]]: JSON response from the Facebook Graph API or None if failed
    """
    try:
        url = f"https://graph.facebook.com/v22.0/{comment_info['comment_id']}/comments"
        payload = {
            "message": message,
            "access_token": page_access_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                data=payload,
                timeout=15.0  # 15 seconds timeout
            )

            if response.status_code == 200:
                logging.info(f"✅ Replied to comment {comment_info['comment_id']} successfully.")
                return response.json()
            else:
                logging.error(f"❌ Failed to reply: {response.status_code} - {response.text}")
                return None

    except httpx.TimeoutException:
        logging.error(f"⏰ Timeout while replying to comment {comment_info['comment_id']}")
        return None
    except Exception as e:
        logging.error(f"❌ Error replying to comment {comment_info['comment_id']}: {str(e)}")
        return None