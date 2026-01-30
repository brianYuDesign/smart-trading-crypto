
import sys
import os
import sqlite3
import logging

# Ensure we can import from src and root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager
from risk_assessment import RiskAssessment

def check_database_columns():
    print("Checking database columns...")
    db_path = 'data/crypto_bot.db'
    
    # Initialize DB manager to trigger migration
    db = DatabaseManager(db_path)
    try:
        db.init_database()
        print("Database initialized/migrated.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    print(f"Columns in users table: {columns}")
    
    required_columns = ['timezone', 'is_active', 'language_code']
    missing = [col for col in required_columns if col not in columns]
    
    if missing:
        print(f"❌ Missing columns in users table: {missing}")
        return False
    else:
        print("✅ All required columns present in users table.")
        return True

def check_risk_assessment_method():
    print("\nChecking RiskAssessment class methods...")
    ra = RiskAssessment()
    
    if hasattr(ra, 'is_in_assessment'):
        print("✅ RiskAssessment has 'is_in_assessment' method.")
        return True
    else:
        print("❌ RiskAssessment MISSING 'is_in_assessment' method.")
        return False

if __name__ == "__main__":
    db_ok = check_database_columns()
    ra_ok = check_risk_assessment_method()
    
    if db_ok and ra_ok:
        print("\n✅ All checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed.")
        sys.exit(1)
