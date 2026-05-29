import os
import sys
import time
import random
from curl_cffi import requests

def run_dispatcher():
    # Introduce architectural jitter (1 to 8 minutes delay)
    # This ensures the API call lands at a completely different time each cycle
    sleep_duration = random.randint(60, 480)
    print(f"[INFO] Injecting timing entropy. Sleeping for {sleep_duration} seconds...")
    time.sleep(sleep_duration)

    auth_token = os.environ.get("DISCORD_TOKEN")
    channel_id = os.environ.get("CHANNEL_ID")
    
    if not auth_token or not channel_id:
        print("[CRITICAL] Missing environment variables.", file=sys.stderr)
        sys.exit(1)

    try:
        with open("message.txt", "r", encoding="utf-8") as file:
            broadcast_content = file.read().strip()
            
        if not broadcast_content:
            print("[CRITICAL] message.txt is empty.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("[CRITICAL] message.txt missing.", file=sys.stderr)
        sys.exit(1)

    api_endpoint = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    
    request_headers = {
        "Authorization": auth_token,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://discord.com",
        "Referer": f"https://discord.com/channels/@me/{channel_id}"
    }
    
    request_payload = {
        "content": broadcast_content,
        "tts": False
    }

    try:
        response = requests.post(
            api_endpoint, 
            json=request_payload, 
            headers=request_headers,
            impersonate="chrome120" 
        )
        
        if response.status_code in [200, 201]:
            print("[INFO] Payload delivered successfully.")
            sys.exit(0)
        else:
            print(f"[ERROR] Request blocked. Status: {response.status_code}", file=sys.stderr)
            print(f"[DEBUG] Raw response: {response.text}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as error:
        print(f"[CRITICAL] Network layer exception: {error}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_dispatcher()
