import os
import sys
import requests

def run_dispatcher():
    # Extract credentials from GitHub Actions secrets
    auth_token = os.environ.get("DISCORD_TOKEN")
    channel_id = os.environ.get("CHANNEL_ID")
    
    if not auth_token or not channel_id:
        print("[CRITICAL] Missing essential configuration values (DISCORD_TOKEN or CHANNEL_ID).", file=sys.stderr)
        sys.exit(1)

    # Read the message payload from message.txt
    try:
        with open("message.txt", "r", encoding="utf-8") as file:
            broadcast_content = file.read().strip()
            
        if not broadcast_content:
            print("[CRITICAL] message.txt is empty.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("[CRITICAL] message.txt not found in the root directory.", file=sys.stderr)
        sys.exit(1)

    api_endpoint = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    
    # Headers optimized to mimic a standard browser payload
    request_headers = {
        "Authorization": auth_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    request_payload = {
        "content": broadcast_content,
        "tts": False
    }

    try:
        response = requests.post(api_endpoint, json=request_payload, headers=request_headers)
        
        if response.status_code == 200:
            print("[INFO] Message dispatched and verified successfully.")
            sys.exit(0)
        else:
            print(f"[ERROR] API Rejected Request. Status Code: {response.status_code}", file=sys.stderr)
            print(f"[DEBUG] Server Response: {response.text}", file=sys.stderr)
            sys.exit(1)
            
    except requests.exceptions.RequestException as error:
        print(f"[CRITICAL] Network request failure encountered: {error}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_dispatcher()
