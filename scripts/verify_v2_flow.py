import requests
import os
import time
import sys

# Add project root to path to import modules if needed (though we interact via HTTP)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
SERVER_URL = "http://localhost:5001/webhook"
ENV_PATH = '.env'

def load_env():
    env_vars = {}
    try:
        with open(ENV_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
                    except ValueError:
                        pass
    except Exception as e:
        print(f"Warning: Could not read .env: {e}")
    return env_vars

env = load_env()
CHAT_ID = env.get('TELEGRAM_CHAT_ID') or env.get('CHAT_ID')

if not CHAT_ID:
    print("❌ Error: TELEGRAM_CHAT_ID not found in .env")
    print("Please set TELEGRAM_CHAT_ID in your .env file to your test account ID.")
    sys.exit(1)

print(f"🚀 Starting V2 Flow Test to Chat ID: {CHAT_ID}")
print(f"📡 Server URL: {SERVER_URL}")

def send_message(text):
    payload = {
        "update_id": int(time.time()),
        "message": {
            "message_id": int(time.time()),
            "from": {
                "id": int(CHAT_ID),
                "is_bot": False,
                "first_name": "TestUser",
                "username": "testuser"
            },
            "chat": {
                "id": int(CHAT_ID),
                "first_name": "TestUser",
                "type": "private"
            },
            "date": int(time.time()),
            "text": text
        }
    }
    
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=10)
        return response
    except requests.exceptions.ConnectionError:
        print("❌ Connect Error: Ensure webhook_server_v2.py is running on port 5001")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error sending '{text}': {e}")
        return None

def run_flow():
    # 1. Start / Welcome
    print("\n[1/5] Testing /start (Welcome Message)...")
    send_message("/start")
    time.sleep(1)

    # 2. Risk Assessment Flow
    print("\n[2/5] Testing Risk Assessment Flow...")
    # Start assessment
    print("  -> Sending /risk_profile")
    send_message("/risk_profile")
    time.sleep(1)
    
    # Answer 10 questions with 'B' (Moderate)
    for i in range(1, 11):
        print(f"  -> Answering Question {i}/10 with 'B'")
        send_message("B")
        time.sleep(0.5) # Wait a bit for processing
    
    # Check profile
    print("  -> verifying profile with /my_profile")
    send_message("/my_profile")
    time.sleep(1)

    # 3. Market Analysis
    print("\n[3/5] Testing Market Analysis...")
    print("  -> Sending /analyze BTC/USDT")
    send_message("/analyze BTC/USDT")
    time.sleep(2) # Analysis involves external API calls

    # 4. Position Management
    print("\n[4/5] Testing Position Management...")
    # Add position
    print("  -> Adding position: 0.1 BTC @ $50000")
    send_message("/add_position BTC/USDT 50000 0.1")
    time.sleep(1)
    
    # View positions
    print("  -> Viewing positions with /positions")
    send_message("/positions")
    time.sleep(1)

    # 5. Done
    print("\n✅ Flow Test Completed!")
    print(f"Check your Telegram (Chat ID: {CHAT_ID}) for the messages.")

if __name__ == "__main__":
    run_flow()
