
import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging to show only important info
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Mock send_message BEFORE importing server to capture output
def mock_send_message(chat_id, text, parse_mode=None):
    print(f"\n[BOT REPLIED to {chat_id}]:\n{text}\n" + "-"*40)
    return {'ok': True}

# Import server and other modules
from src import server
from src import database
from src import risk_assessment

# Apply mocks
server.send_message = mock_send_message
server.TELEGRAM_BOT_TOKEN = "MOCK_TOKEN" # prevent error log

# Use a temporary DB file for isolation
TEST_DB = "simulation.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

print(">>> Initializing Simulation Environment...")
db = database.DatabaseManager(TEST_DB)
server.db = db
risk_assessment.db = db

# Setup Mock User
USER_ID = 123456
CHAT_ID = 123456
USERNAME = "SimUser"

print(f">>> Creating User {USERNAME} (ID: {USER_ID})...")
# init_user only takes user_id, it calls create_or_update_user which might take username but 
# let's just use init_user as it exists.
# We might need to manually insert if we want username, but it's fine.
try:
    db.init_user(USER_ID)
except:
    # If init_user doesn't insert username, we can try to find how to set it.
    pass

def simulate_command(command_text):
    print(f"\n>>> USER SENDS: {command_text}")
    parts = command_text.split()
    command = parts[0].lower()
    
    if command == '/price':
        if len(parts) > 1:
            server.handle_price(CHAT_ID, parts[1])
    elif command == '/analyze':
        if len(parts) > 1:
            server.handle_analyze(CHAT_ID, USER_ID, parts[1])
    elif command == '/my_profile':
        server.handle_my_profile(CHAT_ID, USER_ID)
    elif command == '/alert':
        server.handle_alert(CHAT_ID, USER_ID, parts)
    elif command == '/myalerts':
        server.handle_my_alerts(CHAT_ID, USER_ID)
    elif command == '/risk_profile':
        server.handle_risk_profile(CHAT_ID, USER_ID)
    elif command == '/top':
        server.handle_top(CHAT_ID)
    else:
        print(f"Command {command} not implemented in simulation script.")

# --- SCENARIOS ---

# 0. Test /risk_profile Interactive Flow
print("\n>>> TEST: Interactive /risk_profile Flow")
# Simulate /risk_profile command
simulate_command("/risk_profile")

# Now simulate answers 1-10
questions_count = 10
for i in range(questions_count):
    # Simulate user sending "A" for each question
    # In real server, text messages go to webhook -> process_answer if is_in_assessment
    # Here we need to simulate that logic
    
    # Check if user is in assessment (Mocking server behavior)
    # Note: src.risk_assessment is the module, which contains an instance also named risk_assessment
    if risk_assessment.risk_assessment.is_in_assessment(USER_ID):
        print(f"\n>>> USER SENDS ANSWER: A (for Question {i+1})")
        # In server.py: result = risk_assessment.process_answer(user_id, text)
        result = risk_assessment.risk_assessment.process_answer(USER_ID, "A")
        print(f"[BOT LOGIC]: Process Status = {result['status']}")
        
        # Simulate Bot Reply
        if result['status'] in ['continue', 'completed']:
             mock_send_message(CHAT_ID, result['message'])
        elif result['status'] == 'error':
             mock_send_message(CHAT_ID, f"❌ {result['message']}")
    else:
        print(f"❌ ERROR: User should be in assessment but is_in_assessment returned False at step {i+1}")
        break

# 1. Test Price Fetching (BTC - common ticker)
simulate_command("/price btc")

# 2. Test Price Fetching (Ethereum - full name)
simulate_command("/price ethereum")

# 3. Test Price Fetching (Binance Fallback - BNB)
simulate_command("/price bnb")

# 4. Test Analyze Command (Should use risk profile)
simulate_command("/analyze btc")

# 5. Test My Profile Command (Should show 'Conservative')
simulate_command("/my_profile")

# 6. Test Alert
simulate_command("/alert btc above 200000")

# 7. Test My Alerts
simulate_command("/myalerts")

# 8. Test Top 10
simulate_command("/top")

# Cleanup
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
    print("\n>>> Simulation cleaned up.")
