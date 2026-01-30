
import sys
import os
import logging

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseVerifier")

def verify_database():
    print("Testing src/database.py...")
    
    # Initialize DB (creates file if not exists)
    # Using a test db file to avoid messing with prod
    test_db_path = "test_src_database.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        
    db = DatabaseManager(test_db_path)
    print("✅ DatabaseManager initialized")
    
    # 1. Test User Creation (V2 logic)
    user_id = 999111
    db.create_or_update_user(user_id, username="test_user", first_name="Test", last_name="User")
    user = db.get_user(user_id)
    if user and user['username'] == 'test_user':
        print("✅ User creation verified")
    else:
        print("❌ User creation failed")
        return

    # 2. Test Subscription (V1 ported logic)
    symbol = "BTCUSDT"
    db.add_subscription(user_id, symbol, condition="price > 50000")
    
    subs = db.get_user_subscriptions(user_id)
    if len(subs) == 1 and subs[0]['symbol'] == 'BTCUSDT':
        print("✅ Add/Get Subscription verified")
    else:
        print(f"❌ Subscription verification failed: {subs}")
        return

    # 3. Test Subscription Removal
    db.remove_subscription(user_id, symbol)
    subs = db.get_user_subscriptions(user_id)
    if len(subs) == 0:
        print("✅ Remove Subscription verified")
    else:
        print("❌ Remove Subscription failed")
        return

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    print("\n🎉 All tests passed for src/database.py")

if __name__ == "__main__":
    verify_database()
