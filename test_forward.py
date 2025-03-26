import requests
import json

# URL của backend server
url = "http://localhost:4000/api/webhook"

# Headers
headers = {
    "Content-Type": "application/json"
}

# Data
data = {
    "document_id": "67e257d8003f08970d6aece8",
    "event_type": "message",
    "data": {
        "sender_id": "9705718889448111",
        "recipient_id": "621815067674939",
        "message_id": "m_0q75YHspiA1Uhv6959PQ3-S1p28MPPBNZjBq2JGqr4FVY8ClXTooX0g4oxwFctEhXu9OOE4WB_yJry9rFeKpEA",
        "text": "4545454",
        "timestamp": 1742886874406
    },
    "timestamp": 1742886872.037643,
    "processing_preference": "sync"
}

try:
    # Gửi POST request
    response = requests.post(url, headers=headers, json=data)
    
    # In kết quả
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
    print(f"Response Body: {response.text}")
    
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the server. Make sure the server is running.")
except requests.exceptions.RequestException as e:
    print(f"Error: {str(e)}") 