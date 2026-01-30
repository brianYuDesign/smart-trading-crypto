
import unittest
import json
import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from webhook_server import app

class TestWebhookSimulation(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Suppress logging during tests
        logging.getLogger('webhook_server').setLevel(logging.ERROR)

    @patch('webhook_server.requests.post')
    def test_start_command(self, mock_post):
        """Test /start command"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response

        payload = {
            'update_id': 10001,
            'message': {
                'message_id': 1,
                'from': {'id': 12345, 'first_name': 'TestUser', 'username': 'testuser'},
                'chat': {'id': 12345, 'type': 'private'},
                'date': 1600000000,
                'text': '/start'
            }
        }

        response = self.app.post('/webhook', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify call to Telegram API
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        self.assertIn('sendMessage', args[0])
        self.assertEqual(kwargs['json']['chat_id'], 12345)
        self.assertIn('歡迎使用', kwargs['json']['text'])

    @patch('webhook_server.requests.get')
    @patch('webhook_server.requests.post')
    def test_price_command(self, mock_post, mock_get):
        """Test /price command with mocked CoinGecko response"""
        # Mock CoinGecko response
        mock_cg_response = MagicMock()
        mock_cg_response.status_code = 200
        mock_cg_response.json.return_value = {
            'bitcoin': {'usd': 50000, 'usd_24h_change': 5.5},
            'ethereum': {'usd': 3000, 'usd_24h_change': -2.1},
            'binancecoin': {'usd': 400, 'usd_24h_change': 1.0}
        }
        mock_get.return_value = mock_cg_response

        # Mock Telegram response
        mock_tg_response = MagicMock()
        mock_tg_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_tg_response

        payload = {
            'update_id': 10002,
            'message': {
                'message_id': 2,
                'from': {'id': 12345, 'first_name': 'TestUser'},
                'chat': {'id': 12345, 'type': 'private'},
                'date': 1600000000,
                'text': '/price'
            }
        }

        response = self.app.post('/webhook', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify Telegram message content
        args, kwargs = mock_post.call_args
        text = kwargs['json']['text']
        self.assertIn('Bitcoin', text)
        self.assertIn('$50,000.00', text)

    @patch('webhook_server.requests.get')
    @patch('webhook_server.requests.post')
    def test_market_command(self, mock_post, mock_get):
        """Test /market command"""
        mock_market_response = MagicMock()
        mock_market_response.status_code = 200
        mock_market_response.json.return_value = {
            'data': {
                'total_market_cap': {'usd': 2000000000000},
                'total_volume': {'usd': 100000000000},
                'market_cap_percentage': {'btc': 45.5, 'eth': 18.2}
            }
        }
        mock_get.return_value = mock_market_response

        mock_post.return_value.json.return_value = {'ok': True}

        payload = {
            'update_id': 10003,
            'message': {
                'chat': {'id': 12345},
                'text': '/market'
            }
        }

        response = self.app.post('/webhook', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        args, kwargs = mock_post.call_args
        text = kwargs['json']['text']
        self.assertIn('總市值', text)
        self.assertIn('$2.00T', text)

    @patch('webhook_server.feedparser.parse')
    @patch('webhook_server.requests.post')
    def test_news_command(self, mock_post, mock_feedparser):
        """Test /news command"""
        # Mock feedparser entry as a dictionary-like object
        mock_entry = {
            'title': "Test News Title",
            'link': "http://example.com",
            'summary': "Test summary",
            'description': "Test description"
        }
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_feedparser.return_value = mock_feed

        mock_post.return_value.json.return_value = {'ok': True}

        payload = {
            'update_id': 10004,
            'message': {
                'chat': {'id': 12345},
                'text': '/news'
            }
        }

        response = self.app.post('/webhook', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        args, kwargs = mock_post.call_args
        text = kwargs['json']['text']
        self.assertIn('Test News Title', text)

    @patch('webhook_server.requests.post')
    def test_timezone_command(self, mock_post):
        """Test /timezone command"""
        mock_post.return_value.json.return_value = {'ok': True}

        # 1. No args -> show current
        payload = {
            'update_id': 10005,
            'message': {'chat': {'id': 12345}, 'text': '/timezone'}
        }
        self.app.post('/webhook', data=json.dumps(payload), content_type='application/json')
        args, kwargs = mock_post.call_args
        self.assertIn('當前時區', kwargs['json']['text'])

        # 2. Set valid timezone
        payload['message']['text'] = '/timezone Asia/Tokyo'
        self.app.post('/webhook', data=json.dumps(payload), content_type='application/json')
        args, kwargs = mock_post.call_args
        self.assertIn('時區設定成功', kwargs['json']['text'])
        self.assertIn('Asia/Tokyo', kwargs['json']['text'])

        # 3. Set invalid timezone
        payload['message']['text'] = '/timezone Invalid/Zone'
        self.app.post('/webhook', data=json.dumps(payload), content_type='application/json')
        args, kwargs = mock_post.call_args
        self.assertIn('無效的時區', kwargs['json']['text'])

if __name__ == '__main__':
    unittest.main()
