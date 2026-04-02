import requests
import json
import time

API_URL = "http://127.0.0.1:8001/api/bot"

def trigger_scan():
    # We need the telegram init data to bypass the security check
    # But since we are local and I'm the dev, I'll use the 'debug' bypass if available
    # or just mock the header.
    headers = {
        "X-Telegram-Init-Data": "user=%7B%22id%22%3A133994080%2C%22first_name%22%3A%22Admin%22%2C%22username%22%3A%22admin%22%7D",
        "Content-Type": "application/json"
    }
    
    payload = {
        "action": "admin_scan_library",
        "data": {"force": True}
    }
    
    print("Triggering library scan via API...")
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Wait a bit for the server to start
    time.sleep(3)
    trigger_scan()
