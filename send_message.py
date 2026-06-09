import os
import sys
import time
import random
from curl_cffi import requests

def run_dispatcher():
    # Jitter between 1–5 minutes to avoid pattern detection
    sleep_duration = random.randint(60, 300)
    print(f"[INFO] Sleeping for {sleep_duration} seconds before sending...")
    time.sleep(sleep_duration)

    auth_token = os.environ.get("DISCORD_TOKEN")
    channel_id = os.environ.get("CHANNEL_ID")
    proxy_url = os.environ.get("PROXY_URL", "").strip()

    if not auth_token or not channel_id:
        print("[CRITICAL] Missing DISCORD_TOKEN or CHANNEL_ID.", file=sys.stderr)
        sys.exit(1)

    # Normalize token — add "Bot " prefix only if it's a bot token
    # For user tokens, use as-is (no prefix)
    auth_token = auth_token.strip()

    if proxy_url:
        print(f"[INFO] Proxy configured. Routing through proxy.")
    else:
        print("[WARN] No PROXY_URL set. Using direct connection.")

    try:
        with open("message.txt", "r", encoding="utf-8") as f:
            broadcast_content = f.read().strip()
        if not broadcast_content:
            print("[CRITICAL] message.txt is empty.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("[CRITICAL] message.txt not found.", file=sys.stderr)
        sys.exit(1)

    api_endpoint = f"https://discord.com/api/v10/channels/{channel_id}/messages"

    request_headers = {
        "Authorization": auth_token,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://discord.com",
        "Referer": f"https://discord.com/channels/@me/{channel_id}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    request_payload = {
        "content": broadcast_content,
        "tts": False
    }

    proxies = None
    if proxy_url:
        proxies = proxy_url  # curl_cffi accepts proxy as a string directly

    try:
        if proxies:
            response = requests.post(
                api_endpoint,
                json=request_payload,
                headers=request_headers,
                impersonate="chrome120",
                proxy=proxies,
                timeout=30
            )
        else:
            response = requests.post(
                api_endpoint,
                json=request_payload,
                headers=request_headers,
                impersonate="chrome120",
                timeout=30
            )

        if response.status_code in [200, 201]:
            print("[INFO] Message delivered successfully.")
            sys.exit(0)
        elif response.status_code == 401:
            print("[CRITICAL] 401 Unauthorized — token is invalid or expired.", file=sys.stderr)
            print(f"[DEBUG] Response: {response.text}", file=sys.stderr)
            sys.exit(1)
        elif response.status_code == 403:
            print("[CRITICAL] 403 Forbidden — no permission to send in this channel.", file=sys.stderr)
            print(f"[DEBUG] Response: {response.text}", file=sys.stderr)
            sys.exit(1)
        elif response.status_code == 429:
            retry_after = response.json().get("retry_after", 5)
            print(f"[WARN] Rate limited. Retry after {retry_after}s.", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"[ERROR] Unexpected status: {response.status_code}", file=sys.stderr)
            print(f"[DEBUG] Response: {response.text}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"[CRITICAL] Network exception: {e}", file=sys.stderr)
        # If proxy failed, retry once without proxy
        if proxy_url:
            print("[INFO] Proxy failed. Retrying without proxy...", file=sys.stderr)
            try:
                response = requests.post(
                    api_endpoint,
                    json=request_payload,
                    headers=request_headers,
                    impersonate="chrome120",
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    print("[INFO] Message delivered successfully (direct fallback).")
                    sys.exit(0)
                else:
                    print(f"[ERROR] Fallback also failed. Status: {response.status_code}", file=sys.stderr)
                    sys.exit(1)
            except Exception as e2:
                print(f"[CRITICAL] Fallback also threw exception: {e2}", file=sys.stderr)
                sys.exit(1)
        sys.exit(1)

if __name__ == "__main__":
    run_dispatcher()