
import sqlite3
import os
import sys

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager

def verify_crypto_bot_db_timezone():
    """Verify that the timezone column exists in the users table of crypto_bot.db"""
    db_path = 'crypto_bot.db'
    
    # Initialize DatabaseManager which should trigger migration
    print(f"Initializing DatabaseManager with {db_path}...")
    db_manager = DatabaseManager(db_path=db_path)
    
    print(f"Checking {db_path} for timezone column...")
    if not os.path.exists(db_path):
        print(f"Error: {db_path} does not exist.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'timezone' in columns:
            print("SUCCESS: 'timezone' column found in 'users' table.")
            return True
        else:
            print("FAILURE: 'timezone' column NOT found in 'users' table.")
            print(f"Existing columns: {columns}")
            return False
            
    except sqlite3.OperationalError as e:
        print(f"Error checking table info: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if verify_crypto_bot_db_timezone():
        print("Verification passed!")
        sys.exit(0)
    else:
        print("Verification failed!")
        sys.exit(1)
