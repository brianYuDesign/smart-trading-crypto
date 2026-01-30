
import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock environment variables BEFORE importing webhook_server
os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
os.environ['COINGECKO_API_KEY'] = 'test_key'

# Import the module to test
import webhook_server
from database_manager import db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CommandAnalyzer")

class CommandVerifier:
    def __init__(self):
        self.user_id = 999999
        self.chat_id = 123456
        self.mock_send_message = MagicMock()
        
        # Patch send_message in webhook_server
        self.original_send_message = webhook_server.send_message
        webhook_server.send_message = self.mock_send_message
        
        # Reset DB for test user
        self._reset_db()

    def _reset_db(self):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (self.user_id,))
        cursor.execute("DELETE FROM user_risk_profiles WHERE user_id = ?", (self.user_id,))
        cursor.execute("DELETE FROM positions WHERE user_id = ?", (self.user_id,))
        conn.commit()
        conn.close()

    def verify_command(self, command_name, func, *args):
        logger.info(f"Testing command: {command_name}...")
        self.mock_send_message.reset_mock()
        
        try:
            func(*args)
            
            if self.mock_send_message.called:
                args, _ = self.mock_send_message.call_args
                response_text = args[1]
                logger.info(f"✅ {command_name} successful. Response: {response_text[:50]}...")
                return True
            else:
                logger.error(f"❌ {command_name} failed: No message sent.")
                return False
        except Exception as e:
            logger.error(f"❌ {command_name} failed with exception: {e}")
            return False

    def run_suite(self):
        success_count = 0
        total_tests = 0

        # 1. /start
        total_tests += 1
        if self.verify_command('/start', webhook_server.handle_start, self.chat_id, self.user_id):
            success_count += 1

        # 2. /help
        total_tests += 1
        if self.verify_command('/help', webhook_server.handle_help, self.chat_id):
            success_count += 1
            
        # 3. /price (Mock API first)
        total_tests += 1
        with patch('webhook_server.fetch_crypto_price_multi_source') as mock_price:
            mock_price.return_value = {'source': 'Test', 'price': 50000, 'change_24h': 5.5}
            if self.verify_command('/price BTC', webhook_server.handle_price, self.chat_id, 'BTC'):
                success_count += 1

        # 4. /risk_profile (Start)
        total_tests += 1
        if self.verify_command('/risk_profile', webhook_server.handle_risk_profile, self.chat_id, self.user_id):
            success_count += 1

        # 5. /my_profile (Should fail/warn if not completed, but let's simulate completion)
        # Manually inject a profile for testing
        db.save_risk_profile(self.user_id, 20, [(1, 'B', 2)] * 10)
        
        total_tests += 1
        if self.verify_command('/my_profile', webhook_server.handle_my_profile, self.chat_id, self.user_id):
            success_count += 1

        # 6. /analyze (Requires profile)
        total_tests += 1
        with patch('webhook_server.fetch_crypto_price_multi_source') as mock_price:
            mock_price.return_value = {'source': 'Test', 'price': 50000, 'change_24h': 5.5}
            if self.verify_command('/analyze BTC', webhook_server.handle_analyze, self.chat_id, self.user_id, 'BTC'):
                success_count += 1

        # 7. /add_position
        total_tests += 1
        if self.verify_command('/add_position', webhook_server.handle_add_position, self.chat_id, self.user_id, ['/add_position', 'BTC', '1.5', '40000']):
            success_count += 1

        # 8. /positions
        total_tests += 1
        with patch('webhook_server.fetch_crypto_price_multi_source') as mock_price:
            mock_price.return_value = {'source': 'Test', 'price': 50000, 'change_24h': 5.5}
            if self.verify_command('/positions', webhook_server.handle_positions, self.chat_id, self.user_id):
                success_count += 1
                
        # 9. /top
        total_tests += 1
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [
                {'name': 'Bitcoin', 'symbol': 'btc', 'current_price': 50000, 'price_change_percentage_24h': 5.0}
            ]
            mock_get.return_value = mock_resp
            if self.verify_command('/top', webhook_server.handle_top, self.chat_id):
                success_count += 1

        # 10. /news
        total_tests += 1
        with patch('feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.entries = [
                MagicMock(title="Crypto News 1", link="http://news1.com", published="2023-10-27"),
                MagicMock(title="Crypto News 2", link="http://news2.com", published="2023-10-26")
            ]
            mock_parse.return_value = mock_feed
            if self.verify_command('/news', webhook_server.handle_news, self.chat_id):
                success_count += 1

        print(f"\n📢 Analysis Complete: {success_count}/{total_tests} commands Verified.")
        
        # Cleanup
        # self._reset_db() # Disable cleanup to avoid lock error

if __name__ == "__main__":
    verifier = CommandVerifier()
    verifier.run_suite()
