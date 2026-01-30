
import sys
import os
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.user_manager import UserManager

def verify_migration():
    # Initialize UserManager which should trigger migration
    um = UserManager()
    
    conn = sqlite3.connect('data/users.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    conn.close()
    
    if 'timezone' in columns:
        print("SUCCESS: timezone column exists in users table.")
        return True
    else:
        print("FAILURE: timezone column MISSING in users table.")
        return False

if __name__ == '__main__':
    if verify_migration():
        sys.exit(0)
    else:
        sys.exit(1)
