
import unittest
import sys
import os
import json
from unittest.mock import MagicMock, patch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set env vars
os.environ['TELEGRAM_BOT_TOKEN'] = 'TEST_TOKEN'

from src import server, risk_assessment
from src.database import DatabaseManager

class TestBotHandlers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a test database
        cls.test_db_path = 'test_verify_handlers.db'
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        
        # Init schema manually since file might not be in CWD
        cls.db = DatabaseManager(cls.test_db_path)
        
        # Patch server's db and risk_assessment's db to use our test database instance
        server.db = cls.db
        risk_assessment.db = cls.db
        
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database_schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                conn = cls.db.get_connection()
                conn.executescript(f.read())
                conn.commit()
                conn.close()
        
        # Test User
        cls.user_id = 123456789
        cls.chat_id = 987654321

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def setUp(self):
        # Reset user state if needed
        pass

    @patch('src.server.send_message')
    def test_01_start(self, mock_send):
        logger.info("Testing /start...")
        server.handle_start(self.chat_id, self.user_id)
        mock_send.assert_called()
        args = mock_send.call_args[0]
        self.assertIn("歡迎使用", args[1])
        logger.info("✅ /start passed")

    @patch('src.server.send_message')
    def test_02_help(self, mock_send):
        logger.info("Testing /help...")
        server.handle_help(self.chat_id)
        mock_send.assert_called()
        args = mock_send.call_args[0]
        self.assertIn("/alert", args[1]) # Check new commands are listed
        logger.info("✅ /help passed")

    @patch('src.server.send_message')
    @patch('src.server.fetch_crypto_price_multi_source')
    def test_03_price(self, mock_price, mock_send):
        logger.info("Testing /price...")
        mock_price.return_value = {'source': 'Test', 'price': 50000.0, 'change_24h': 5.0}
        
        server.handle_price(self.chat_id, 'BTC')
        
        mock_send.assert_called()
        text = mock_send.call_args[0][1]
        self.assertIn("50,000.00", text)
        logger.info("✅ /price passed")

    @patch('src.server.send_message')
    @patch('src.server.fetch_crypto_price_multi_source')
    def test_04_add_position(self, mock_price, mock_send):
        logger.info("Testing /add_position...")
        # Add position: /add_position BTC 0.1 40000
        server.handle_add_position(self.chat_id, self.user_id, ['/add_position', 'BTC', '0.1', '40000'])
        
        mock_send.assert_called()
        text = mock_send.call_args[0][1]
        self.assertIn("已新增持倉", text)
        logger.info("✅ /add_position passed")

    @patch('src.server.send_message')
    @patch('src.server.fetch_crypto_price_multi_source')
    def test_05_positions(self, mock_price, mock_send):
        logger.info("Testing /positions...")
        mock_price.return_value = {'source': 'Test', 'price': 50000.0, 'change_24h': 5.0}
        
        server.handle_positions(self.chat_id, self.user_id)
        
        mock_send.assert_called()
        text = mock_send.call_args[0][1]
        self.assertIn("BTC", text)
        self.assertIn("盈虧", text)
        logger.info("✅ /positions passed")

    @patch('src.server.send_message')
    @patch('src.server.fetch_crypto_price_multi_source')
    def test_06_alert_commands(self, mock_price, mock_send):
        logger.info("Testing Alert Commands...")
        mock_price.return_value = {'source': 'Test', 'price': 50000.0, 'change_24h': 5.0}

        # 1. /alert BTC 55000 (Above logic check)
        # Current 50000, Target 55000 -> "漲破"
        server.handle_alert(self.chat_id, self.user_id, ['/alert', 'BTC', '55000'])
        mock_send.assert_called()
        text = mock_send.call_args[0][1]
        self.assertIn("已設定提醒", text)
        self.assertIn("漲破", text)
        
        # Capture ID? We can check DB or parse message. testing check DB directly is better
        watchlist = self.db.get_active_watchlist(self.user_id)
        self.assertEqual(len(watchlist), 1)
        alert_id = watchlist[0]['watchlist_id']

        # 2. /myalerts
        server.handle_my_alerts(self.chat_id, self.user_id)
        text = mock_send.call_args[0][1]
        self.assertIn("BTC", text)
        self.assertIn("55,000.00", text)

        # 3. /del_alert
        server.handle_del_alert(self.chat_id, self.user_id, ['/del_alert', str(alert_id)])
        text = mock_send.call_args[0][1]
        self.assertIn("已刪除提醒", text)

        # Verify deletion
        watchlist = self.db.get_active_watchlist(self.user_id)
        self.assertEqual(len(watchlist), 0)
        
        logger.info("✅ Alert commands passed")

    @patch('src.server.send_message')
    @patch('src.server.requests.get')
    def test_07_top(self, mock_get, mock_send):
        logger.info("Testing /top...")
        # Mock CoinGecko response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {'name': 'Bitcoin', 'symbol': 'btc', 'current_price': 50000, 'price_change_percentage_24h': 5.0}
        ]
        mock_get.return_value = mock_resp

        server.handle_top(self.chat_id)
        
        mock_send.assert_called()
        text = mock_send.call_args[0][1]
        self.assertIn("Bitcoin", text)
        logger.info("✅ /top passed")

    @patch('src.server.send_message')
    def test_08_risk_profile_flow(self, mock_send):
        logger.info("Testing /risk_profile flow...")
        # Start
        server.handle_risk_profile(self.chat_id, self.user_id)
        mock_send.assert_called()
        # The question might be "您的年齡是？" or similar. Checking risk_assessment.py logic via output.
        # It's actually "您的加密貨幣投資經驗？"
        self.assertIn("經驗", mock_send.call_args[0][1])

        # We are not testing the full interactive flow here deeply, just that it starts
        # Deep testing would require mocking state in risk_assessment module which is in memory
        logger.info("✅ /risk_profile start passed")

    @patch('src.server.send_message')
    def test_09_my_profile(self, mock_send):
        """測試 /my_profile 指令"""
        logger.info("Testing /my_profile...")
        # First ensure user has a profile (manually set in db)
        self.db.save_risk_profile(self.user_id, 20, [])  # Score 20 -> 穩健型
        
        server.handle_my_profile(self.chat_id, self.user_id)
        mock_send.assert_called()
        self.assertIn("穩健型", mock_send.call_args[0][1])
        logger.info("✅ /my_profile passed")

    @patch('src.server.send_message')
    @patch('src.server.fetch_crypto_price_multi_source')
    def test_10_analyze(self, mock_price, mock_send):
        logger.info("Testing /analyze...")
        mock_price.return_value = {'source': 'Test', 'price': 50000.0, 'change_24h': 5.0}
        
        # User already has risk profile from test_09
        server.handle_analyze(self.chat_id, self.user_id, 'BTC')
        
        mock_send.assert_called()
        text = mock_send.call_args[0][1]
        self.assertIn("建議", text)
        logger.info("✅ /analyze passed")

if __name__ == '__main__':
    unittest.main()
