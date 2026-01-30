
import sys
import os
import logging

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_modules():
    logger.info("Verifying migrated modules...")
    
    try:
        # 1. Verify Database Import
        logger.info("Importing src.database...")
        from src.database import db, DatabaseManager
        logger.info("Successfully imported src.database")
        
        # Initialize DB for other modules
        db.init_database()
        
        # 2. Verify Risk Assessment
        logger.info("Importing src.risk_assessment...")
        from src.risk_assessment import RiskAssessment
        risk_assessor = RiskAssessment()
        logger.info("Successfully initialized RiskAssessment")
        
        # 3. Verify Trading Strategy
        logger.info("Importing src.trading_strategy...")
        from src.trading_strategy import TradingStrategy
        strategy = TradingStrategy()
        logger.info("Successfully initialized TradingStrategy")
        
        # 4. Verify Market Monitor
        logger.info("Importing src.market_monitor...")
        from src.market_monitor import MarketMonitor
        # Pass a dummy token for verification purposes
        monitor = MarketMonitor(bot_token="dummy_token_for_verification")
        logger.info("Successfully initialized MarketMonitor")
        
        logger.info("ALL MODULES VERIFIED SUCCESSFULLY")
        return True
        
    except ImportError as e:
        logger.error(f"Import Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_modules():
        sys.exit(0)
    else:
        sys.exit(1)
