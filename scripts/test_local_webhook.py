import requests
import os
import json
import time

# 載入設定 (簡單讀取 .env)
env_vars = {}
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key] = value
except Exception as e:
    print(f"無法讀取 .env: {e}")
    exit(1)

CHAT_ID = env_vars.get('TELEGRAM_CHAT_ID') or env_vars.get('CHAT_ID')
if not CHAT_ID:
    print("錯誤: .env 中找不到 TELEGRAM_CHAT_ID")
    exit(1)

# 測試指令
COMMANDS = ['/price', '/market', '/news', '/help']

SERVER_URL = "http://localhost:10000/webhook"

def send_mock_update(command):
    payload = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": int(CHAT_ID),
                "is_bot": False,
                "first_name": "TestUser",
            },
            "chat": {
                "id": int(CHAT_ID),
                "first_name": "TestUser",
                "type": "private"
            },
            "date": int(time.time()),
            "text": command
        }
    }
    
    print(f"傳送指令: {command} ...")
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=5)
        print(f"伺服器回應: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"請求失敗: {e}")

if __name__ == "__main__":
    print(f"開始測試，目標用戶 ID: {CHAT_ID}")
    
    # 測試 /start
    send_mock_update('/start')
    time.sleep(1) 
    
    # 測試 /price
    send_mock_update('/price')
