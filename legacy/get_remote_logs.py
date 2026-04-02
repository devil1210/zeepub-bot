import requests
import json

API_URL = "http://127.0.0.1:8001/api/bot"

def get_logs():
    headers = {
        "X-Telegram-Init-Data": "user=%7B%22id%22%3A133994080%2C%22first_name%22%3A%22Admin%22%2C%22username%22%3A%22admin%22%7D",
        "Content-Type": "application/json"
    }
    
    payload = {
        "action": "admin_get_system_logs",
        "data": {}
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("--- SYSTEM LOGS ---")
                for log in data.get("logs", []):
                    print(f"[{log['time']}] {log['level']}: {log['msg']}")
                print("-------------------")
            else:
                print(f"API Error: {data.get('message')}")
        else:
            print(f"HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_logs()
