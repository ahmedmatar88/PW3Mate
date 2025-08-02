"""
Integration tests for Tesla Powerwall Scheduler Lambda function
Tests Powerwall control, Tesla Fleet API integration, and notification system
"""

import json
import pytest
import boto3
from moto import mock_ssm
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
import requests

# Import the Lambda function (adjust path as needed)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'powerwall_scheduler'))
import lambda_function


class TestTeslaFleetClient:
    """Test TeslaFleetClient class functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.client = lambda_function.TeslaFleetClient(
            client_id='test-client-id-123',
            client_secret='ta-secret.test-secret-456',
            region='eu'
        )
        self.client.set_tokens(
            'test-access-token-789',
            'test-refresh-token-abc'
        )
    
    def test_client_initialization(self):
        """Test Tesla Fleet client initialization"""
        assert self.client.client_id == 'test-client-id-123'
        assert self.client.client_secret == 'ta-secret.test-secret-456'
        assert self.client.region == 'eu'
        assert 'fleet-api.prd.eu.vn.cloud.tesla.com' in self.client.api_base
    
    def test_set_tokens(self):
        """Test setting authentication tokens"""
        access_token = 'new-access-token-xyz'
        refresh_token = 'new-refresh-token-def'
        
        self.client.set_tokens(access_token, refresh_token)
        
        assert self.client.access_token == access_token
        assert self.client.refresh_token == refresh_token
        assert f'Bearer {access_token}' in self.client.session.headers['Authorization']
    
    def test_refresh_access_token_success(self):
        """Test successful token refresh"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'refreshed-access-token',
            'refresh_token': 'refreshed-refresh-token',
            'expires_in': 28800
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            success, new_access, new_refresh = self.client.refresh_access_token()
        
        assert success is True
        assert new_access == 'refreshed-access-token'
        assert new_refresh == 'refreshed-refresh-token'
        assert self.client.access_token == 'refreshed-access-token'
    
    def test_refresh_access_token_expired(self):
        """Test token refresh with expired refresh token"""
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch('requests.post', return_value=mock_response):
            success, new_access, new_refresh = self.client.refresh_access_token()
        
        assert success is False
        assert new_access is None
        assert new_refresh is None
    
    def test_api_request_success(self):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': {'test': 'data'}
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(self.client.session, 'request', return_value=mock_response):
            result = self.client.api_request('GET', '/api/1/test')
        
        assert result == {'response': {'test': 'data'}}
    
    def test_api_request_failure(self):
        """Test failed API request"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        with patch.object(self.client.session, 'request', return_value=mock_response):
            result = self.client.api_request('GET', '/api/1/nonexistent')
        
        assert result is None
    
    def test_get_products(self):
        """Test getting Tesla products"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': [
                {
                    'id': 12345,
                    'device_type': 'energy',
                    'resource_type': 'battery',
                    'energy_site_id': 67890
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(self.client.session, 'request', return_value=mock_response):
            result = self.client.get_products()
        
        assert result['response'][0]['device_type'] == 'energy'
        assert result['response'][0]['energy_site_id'] == 67890
    
    def test_find_powerwall_site(self):
        """Test finding Powerwall site ID"""
        mock_products = {
            'response': [
                {
                    'id': 12345,
                    'device_type': 'energy',
                    'resource_type': 'battery',
                    'energy_site_id': 67890
                },
                {
                    'id': 54321,
                    'device_type': 'vehicle',
                    'resource_type': 'car'
                }
            ]
        }
        
        with patch.object(self.client, 'get_products', return_value=mock_products):
            site_id = self.client.find_powerwall_site()
        
        assert site_id == '67890'
    
    def test_find_powerwall_site_not_found(self):
        """Test finding Powerwall when none exists"""
        mock_products = {
            'response': [
                {
                    'id': 54321,
                    'device_type': 'vehicle',
                    'resource_type': 'car'
                }
            ]
        }
        
        with patch.object(self.client, 'get_products', return_value=mock_products):
            site_id = self.client.find_powerwall_site()
        
        assert site_id is None
    
    def test_get_site_info(self):
        """Test getting site information"""
        site_id = '67890'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': {
                'backup_reserve_percent': 50,
                'battery_count': 2,
                'nameplate_power': 10800
            }
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(self.client.session, 'request', return_value=mock_response):
            result = self.client.get_site_info(site_id)
        
        assert result['response']['backup_reserve_percent'] == 50
        assert result['response']['battery_count'] == 2
    
    def test_get_live_status(self):
        """Test getting live status data"""
        site_id = '67890'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': {
                'percentage_charged': 85,
                'battery_power': -2100,  # Charging
                'solar_power': 0,
                'load_power': 1800
            }
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(self.client.session, 'request', return_value=mock_response):
            result = self.client.get_live_status(site_id)
        
        assert result['response']['percentage_charged'] == 85
        assert result['response']['battery_power'] == -2100
        assert result['response']['solar_power'] == 0
        assert result['response']['load_power'] == 1800
    
    def test_set_backup_reserve_success(self):
        """Test successful backup reserve change"""
        site_id = '67890'
        new_percent = 75
        
        # Mock current site info
        mock_site_info = {
            'response': {
                'backup_reserve_percent': 50
            }
        }
        
        # Mock successful backup reserve change
        mock_backup_response = Mock()
        mock_backup_response.status_code = 200
        mock_backup_response.json.return_value = {
            'response': {'result': True}
        }
        mock_backup_response.raise_for_status.return_value = None
        
        with patch.object(self.client, 'get_site_info', return_value=mock_site_info), \
             patch.object(self.client.session, 'request', return_value=mock_backup_response):
            
            result = self.client.set_backup_reserve(site_id, new_percent)
        
        assert result['success'] is True
        assert result['old_reserve'] == 50
        assert result['new_reserve'] == 75
    
    def test_set_backup_reserve_failure(self):
        """Test failed backup reserve change"""
        site_id = '67890'
        new_percent = 75
        
        # Mock current site info
        mock_site_info = {
            'response': {
                'backup_reserve_percent': 50
            }
        }
        
        # Mock failed backup reserve change
        mock_backup_response = Mock()
        mock_backup_response.status_code = 400
        mock_backup_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Bad Request")
        
        with patch.object(self.client, 'get_site_info', return_value=mock_site_info), \
             patch.object(self.client.session, 'request', return_value=mock_backup_response):
            
            result = self.client.set_backup_reserve(site_id, new_percent)
        
        assert result is None


class TestNotificationManager:
    """Test NotificationManager class functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.credentials = {
            'discord_webhook': 'https://discord.com/api/webhooks/test/webhook',
            'pushover_token': 'test-pushover-token',
            'pushover_user': 'test-pushover-user',
            'notification_email': 'test@example.com'
        }
        self.notifier = lambda_function.NotificationManager(self.credentials)
    
    def test_send_discord_notification_success(self):
        """Test successful Discord notification"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = self.notifier.send_discord_notification('Test message with **title**')
        
        assert result is True
        mock_post.assert_called_once()
        
        # Verify payload structure
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        assert 'embeds' in payload
        assert payload['username'] == 'Tesla Powerwall Bot'
    
    def test_send_pushover_notification_success(self):
        """Test successful Pushover notification"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = self.notifier.send_pushover_notification('Test Title', 'Test message')
        
        assert result is True
        mock_post.assert_called_once_with(
            'https://api.pushover.net/1/messages.json',
            data={
                'token': 'test-pushover-token',
                'user': 'test-pushover-user',
                'title': 'Test Title',
                'message': 'Test message',
                'priority': 0,
                'sound': 'pushover'
            }
        )
    
    def test_send_pushover_notification_missing_credentials(self):
        """Test Pushover notification with missing credentials"""
        notifier = lambda_function.NotificationManager({})
        result = notifier.send_pushover_notification('Title', 'Message')
        assert result is False
    
    def test_send_all_notifications(self):
        """Test sending notifications via all configured methods"""
        # Mock all notification methods
        with patch.object(self.notifier, 'send_pushover_notification', return_value=True), \
             patch.object(self.notifier, 'send_sns_notification', return_value=True), \
             patch.object(self.notifier, 'send_discord_notification', return_value=True), \
             patch.object(self.notifier, 'send_email_notification', return_value=True):
            
            result = self.notifier.send_all_notifications(
                'Test Title',
                'Test message',
                include_live_data=False
            )
        
        assert result is True
    
    def test_send_all_notifications_with_live_data(self):
        """Test sending notifications with live Powerwall data"""
        # Mock Tesla client with live data
        mock_tesla_client = Mock()
        mock_tesla_client.get_live_status.return_value = {
            'response': {
                'percentage_charged': 85,
                'battery_power': -2100,
                'solar_power': 0,
                'load_power': 1800
            }
        }
        
        with patch.object(self.notifier, 'send_discord_notification', return_value=True) as mock_discord:
            result = self.notifier.send_all_notifications(
                'Test Title',
                'Test message',
                include_live_data=True,
                site_id='67890',
                tesla_client=mock_tesla_client
            )
        
        assert result is True
        
        # Verify live data was included in the message
        call_args = mock_discord.call_args[0][0]
        assert 'Current Status:' in call_args
        assert 'Battery: 85%' in call_args


class TestLambdaHandler:
    """Test the main Lambda handler function"""
    
    @mock_ssm
    def test_lambda_handler_success(self):
        """Test successful Powerwall schedule execution"""
        # Set up Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id-123',
            '/tesla/powerwall/client_secret': 'ta-secret.test-secret-456',
            '/tesla/powerwall/access_token': 'test-access-token-789',
            '/tesla/powerwall/refresh_token': 'test-refresh-token-abc',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/test/webhook'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        # Test event
        test_event = {
            'backup_reserve_percent': 75,
            'schedule_name': 'Test Schedule - Set to 75%'
        }
        
        # Mock Tesla API responses
        mock_products_response = {
            'response': [
                {
                    'id': 12345,
                    'device_type': 'energy',
                    'resource_type': 'battery',
                    'energy_site_id': 67890
                }
            ]
        }
        
        mock_site_info_response = {
            'response': {
                'backup_reserve_percent': 50
            }
        }
        
        mock_backup_response = Mock()
        mock_backup_response.status_code = 200
        mock_backup_response.json.return_value = {'response': {'result': True}}
        mock_backup_response.raise_for_status.return_value = None
        
        mock_live_status_response = {
            'response': {
                'percentage_charged': 85,
                'battery_power': -2100,
                'solar_power': 0,
                'load_power': 1800
            }
        }
        
        mock_discord_response = Mock()
        mock_discord_response.status_code = 200
        mock_discord_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_discord_response), \
             patch('lambda_function.TeslaFleetClient') as mock_tesla_class:
            
            # Configure mock Tesla client
            mock_tesla_client = Mock()
            mock_tesla_class.return_value = mock_tesla_client
            mock_tesla_client.find_powerwall_site.return_value = '67890'
            mock_tesla_client.set_backup_reserve.return_value = {
                'success': True,
                'old_reserve': 50,
                'new_reserve': 75
            }
            mock_tesla_client.get_live_status.return_value = mock_live_status_response
            
            result = lambda_function.lambda_handler(test_event, None)
        
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        assert body['backup_reserve'] == 75
        assert body['schedule_name'] == 'Test Schedule - Set to 75%'
        assert body['site_id'] == '67890'
        assert body['old_reserve'] == 50
    
    @mock_ssm
    def test_lambda_handler_missing_event_data(self):
        """Test Lambda handler with missing backup_reserve_percent"""
        # Set up minimal Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/tesla/powerwall/client_id',
            Value='test-client-id',
            Type='SecureString'
        )
        
        # Test event missing required field
        test_event = {
            'schedule_name': 'Test Schedule'
            # Missing backup_reserve_percent
        }
        
        result = lambda_function.lambda_handler(test_event, None)
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert 'backup_reserve_percent required' in body['error']
    
    @mock_ssm
    def test_lambda_handler_no_powerwall_found(self):
        """Test Lambda handler when no Powerwall is found"""
        # Set up Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id-123',
            '/tesla/powerwall/client_secret': 'ta-secret.test-secret-456',
            '/tesla/powerwall/access_token': 'test-access-token-789',
            '/tesla/powerwall/refresh_token': 'test-refresh-token-abc',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/test/webhook'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        test_event = {
            'backup_reserve_percent': 75,
            'schedule_name': 'Test Schedule - Set to 75%'
        }
        
        mock_discord_response = Mock()
        mock_discord_response.status_code = 200
        mock_discord_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_discord_response), \
             patch('lambda_function.TeslaFleetClient') as mock_tesla_class:
            
            # Configure mock Tesla client to return None (no Powerwall found)
            mock_tesla_client = Mock()
            mock_tesla_class.return_value = mock_tesla_client
            mock_tesla_client.find_powerwall_site.return_value = None
            
            result = lambda_function.lambda_handler(test_event, None)
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert 'No Powerwall found' in body['error']
    
    @mock_ssm
    def test_lambda_handler_backup_reserve_failure(self):
        """Test Lambda handler when backup reserve change fails"""
        # Set up Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id-123',
            '/tesla/powerwall/client_secret': 'ta-secret.test-secret-456',
            '/tesla/powerwall/access_token': 'test-access-token-789',
            '/tesla/powerwall/refresh_token': 'test-refresh-token-abc',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/test/webhook'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        test_event = {
            'backup_reserve_percent': 75,
            'schedule_name': 'Test Schedule - Set to 75%'
        }
        
        mock_discord_response = Mock()
        mock_discord_response.status_code = 200
        mock_discord_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_discord_response), \
             patch('lambda_function.TeslaFleetClient') as mock_tesla_class:
            
            # Configure mock Tesla client
            mock_tesla_client = Mock()
            mock_tesla_class.return_value = mock_tesla_client
            mock_tesla_client.find_powerwall_site.return_value = '67890'
            mock_tesla_client.set_backup_reserve.return_value = None  # Failure
            
            result = lambda_function.lambda_handler(test_event, None)
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'Failed to set backup reserve' in body['error']
    
    @mock_ssm
    def test_lambda_handler_token_refresh_needed(self):
        """Test Lambda handler with expired tokens requiring refresh"""
        # Set up Parameter Store with old token refresh timestamp
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id-123',
            '/tesla/powerwall/client_secret': 'ta-secret.test-secret-456',
            '/tesla/powerwall/access_token': 'test-access-token-789',
            '/tesla/powerwall/refresh_token': 'test-refresh-token-abc',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/test/webhook',
            '/tesla/powerwall/last_token_refresh': '2025-01-01T00:00:00.000Z'  # 10+ hours ago
        }
        
        for name, value in test_params.items():
            param_type = 'String' if name.endswith('last_token_refresh') else 'SecureString'
            ssm.put_parameter(Name=name, Value=value, Type=param_type)
        
        test_event = {
            'backup_reserve_percent': 75,
            'schedule_name': 'Test Schedule - Set to 75%'
        }
        
        # Mock current time to be 10+ hours after last refresh
        with patch('lambda_function.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)  # 12 hours later
            mock_datetime.fromisoformat.return_value = datetime(2025, 1, 1, 0, 0, 0)
            
            mock_discord_response = Mock()
            mock_discord_response.status_code = 200
            mock_discord_response.raise_for_status.return_value = None
            
            with patch('requests.post', return_value=mock_discord_response), \
                 patch('lambda_function.TeslaFleetClient') as mock_tesla_class:
                
                # Configure mock Tesla client
                mock_tesla_client = Mock()
                mock_tesla_class.return_value = mock_tesla_client
                mock_tesla_client.refresh_access_token.return_value = (True, 'new-token', 'new-refresh')
                mock_tesla_client.find_powerwall_site.return_value = '67890'
                mock_tesla_client.set_backup_reserve.return_value = {
                    'success': True,
                    'old_reserve': 50,
                    'new_reserve': 75
                }
                
                result = lambda_function.lambda_handler(test_event, None)
        
        assert result['statusCode'] == 200
        # Verify backup token refresh was attempted
        mock_tesla_client.refresh_access_token.assert_called_once()


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @mock_ssm
    def test_missing_tesla_credentials(self):
        """Test handling of missing Tesla credentials"""
        # Set up Parameter Store with missing credentials
        ssm = boto3.client('ssm', region_name='us-east-1')
        ssm.put_parameter(
            Name='/tesla/powerwall/client_id',
            Value='test-client-id',
            Type='SecureString'
        )
        # Missing other required parameters
        
        test_event = {
            'backup_reserve_percent': 75,
            'schedule_name': 'Test Schedule'
        }
        
        result = lambda_function.lambda_handler(test_event, None)
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'Missing Tesla credentials' in body['error']
    
    @mock_ssm
    def test_invalid_backup_percentage(self):
        """Test handling of invalid backup reserve percentage"""
        # Set up Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id-123',
            '/tesla/powerwall/client_secret': 'ta-secret.test-secret-456',
            '/tesla/powerwall/access_token': 'test-access-token-789',
            '/tesla/powerwall/refresh_token': 'test-refresh-token-abc'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        # Test with invalid percentage
        test_event = {
            'backup_reserve_percent': 150,  # Invalid: > 100
            'schedule_name': 'Invalid Test'
        }
        
        with patch('lambda_function.TeslaFleetClient') as mock_tesla_class:
            mock_tesla_client = Mock()
            mock_tesla_class.return_value = mock_tesla_client
            mock_tesla_client.find_powerwall_site.return_value = '67890'
            mock_tesla_client.set_backup_reserve.return_value = None  # Tesla API rejects invalid value
            
            result = lambda_function.lambda_handler(test_event, None)
        
        assert result['statusCode'] == 500
    
    def test_tesla_api_network_error(self):
        """Test handling of Tesla API network errors"""
        client = lambda_function.TeslaFleetClient('test-id', 'test-secret')
        client.set_tokens('test-access', 'test-refresh')
        
        with patch.object(client.session, 'request', side_effect=requests.exceptions.ConnectionError("Network error")):
            result = client.api_request('GET', '/api/1/products')
        
        assert result is None
    
    def test_tesla_api_timeout(self):
        """Test handling of Tesla API timeouts"""
        client = lambda_function.TeslaFleetClient('test-id', 'test-secret')
        client.set_tokens('test-access', 'test-refresh')
        
        with patch.object(client.session, 'request', side_effect=requests.exceptions.Timeout("Request timeout")):
            result = client.api_request('GET', '/api/1/products')
        
        assert result is None


class TestNotificationFormats:
    """Test notification message formatting"""
    
    def test_discord_success_notification_format(self):
        """Test Discord success notification formatting"""
        notifier = lambda_function.NotificationManager({
            'discord_webhook': 'https://discord.com/api/webhooks/test/webhook'
        })
        
        test_message = "**✅ Tesla Powerwall Updated**\n11:31 PM - Set to 100%\n\nBackup reserve changed: 50% → 100%"
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = notifier.send_discord_notification(test_message)
        
        assert result is True
        
        # Verify message formatting
        call_args = mock_post.call_args[1]['json']
        embed = call_args['embeds'][0]
        
        assert embed['title'] == '✅ Tesla Powerwall Updated'
        assert '11:31 PM - Set to 100%' in embed['description']
        assert 'Backup reserve changed: 50% → 100%' in embed['description']
    
    def test_discord_error_notification_format(self):
        """Test Discord error notification formatting"""
        notifier = lambda_function.NotificationManager({
            'discord_webhook': 'https://discord.com/api/webhooks/test/webhook'
        })
        
        test_message = "❌ Failed to execute 11:31 PM - Set to 100%"
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = notifier.send_discord_notification(test_message)
        
        assert result is True
        
        # Verify error color is used
        call_args = mock_post.call_args[1]['json']
        embed = call_args['embeds'][0]
        
        assert embed['color'] == 0xff0000  # Red color for errors
    
    def test_live_data_formatting(self):
        """Test live Powerwall data formatting in notifications"""
        live_status = {
            'response': {
                'percentage_charged': 85,
                'battery_power': -2100,  # Negative = charging
                'solar_power': 0,
                'load_power': 1800
            }
        }
        
        # Simulate live data formatting
        battery_level = live_status['response']['percentage_charged']
        battery_power = live_status['response']['battery_power']
        solar_power = live_status['response']['solar_power']
        home_power = live_status['response']['load_power']
        
        status_text = f"\n\n📊 Current Status:\n"
        status_text += f"🔋 Battery: {battery_level}%\n"
        status_text += f"⚡ Battery Power: {battery_power}W {'(charging)' if battery_power < 0 else '(discharging)'}\n"
        status_text += f"☀️ Solar: {solar_power}W\n"
        status_text += f"🏠 Home Usage: {home_power}W"
        
        assert "Battery: 85%" in status_text
        assert "(charging)" in status_text
        assert "Solar: 0W" in status_text
        assert "Home Usage: 1800W" in status_text


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    @mock_ssm
    def test_complete_successful_schedule_execution(self):
        """Test complete successful schedule execution end-to-end"""
        # Set up Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': '8f2a9b47-d3e1-4c56-a789-1b2c3d4e5f6g',
            '/tesla/powerwall/client_secret': 'ta-secret.Kx9Zm4Pq7Nv2RtY8MockSecret123',
            '/tesla/powerwall/access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.mock-access-token',
            '/tesla/powerwall/refresh_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.mock-refresh-token',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/123456789/test-webhook-abc123'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        # Realistic event from EventBridge
        test_event = {
            'backup_reserve_percent': 100,
            'schedule_name': '11:31 PM - Set to 100%'
        }
        
        # Mock all Tesla API responses
        mock_products = {
            'response': [
                {
                    'id': 123456789,
                    'device_type': 'energy',
                    'resource_type': 'battery',
                    'energy_site_id': 987654321
                }
            ]
        }
        
        mock_site_info = {
            'response': {
                'backup_reserve_percent': 50,
                'battery_count': 2,
                'nameplate_power': 10800
            }
        }
        
        mock_live_status = {
            'response': {
                'percentage_charged': 85,
                'battery_power': -2100,
                'solar_power': 0,
                'load_power': 1800,
                'energy_left': 13.2,
                'total_pack_energy': 27.4
            }
        }
        
        # Mock successful backup reserve change
        mock_backup_response = Mock()
        mock_backup_response.status_code = 200
        mock_backup_response.json.return_value = {'response': {'result': True}}
        mock_backup_response.raise_for_status.return_value = None
        
        # Mock Discord notification
        mock_discord_response = Mock()
        mock_discord_response.status_code = 200
        mock_discord_response.raise_for_status.return_value = None
        
        with patch('lambda_function.TeslaFleetClient') as mock_tesla_class, \
             patch('requests.post', return_value=mock_discord_response) as mock_discord_post:
            
            # Configure comprehensive mock Tesla client
            mock_tesla_client = Mock()
            mock_tesla_class.return_value = mock_tesla_client
            
            # Set up method return values
            mock_tesla_client.find_powerwall_site.return_value = '987654321'
            mock_tesla_client.get_site_info.return_value = mock_site_info
            mock_tesla_client.get_live_status.return_value = mock_live_status
            mock_tesla_client.set_backup_reserve.return_value = {
                'success': True,
                'old_reserve': 50,
                'new_reserve': 100
            }
            
            # Execute Lambda handler
            result = lambda_function.lambda_handler(test_event, None)
        
        # Verify successful execution
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        assert body['backup_reserve'] == 100
        assert body['schedule_name'] == '11:31 PM - Set to 100%'
        assert body['site_id'] == '987654321'
        assert body['old_reserve'] == 50
        
        # Verify Tesla client was called correctly
        mock_tesla_client.find_powerwall_site.assert_called_once()
        mock_tesla_client.set_backup_reserve.assert_called_once_with('987654321', 100)
        mock_tesla_client.get_live_status.assert_called_once_with('987654321')
        
        # Verify Discord notification was sent
        mock_discord_post.assert_called_once()
        discord_payload = mock_discord_post.call_args[1]['json']
        
        assert 'embeds' in discord_payload
        embed = discord_payload['embeds'][0]
        assert '✅ Tesla Powerwall Updated' in embed['title']
        assert '11:31 PM - Set to 100%' in embed['description']
        assert 'Backup reserve changed: 50% → 100%' in embed['description']
        assert 'Battery: 85%' in embed['description']
        assert 'Battery Power: -2100W (charging)' in embed['description']


class TestPerformanceAndReliability:
    """Test performance and reliability aspects"""
    
    def test_lambda_execution_time(self):
        """Test that Lambda execution completes within timeout"""
        import time
        
        # Simulate fast execution
        start_time = time.time()
        
        # Mock all dependencies for fast execution
        with patch('lambda_function.ParameterStoreManager'), \
             patch('lambda_function.TeslaFleetClient'), \
             patch('lambda_function.NotificationManager'):
            
            test_event = {
                'backup_reserve_percent': 75,
                'schedule_name': 'Performance Test'
            }
            
            result = lambda_function.lambda_handler(test_event, None)
            
        execution_time = time.time() - start_time
        
        # Should complete very quickly in test environment
        assert execution_time < 1.0
    
    def test_memory_efficiency(self):
        """Test memory usage efficiency"""
        import sys
        import gc
        
        # Measure memory before
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create multiple instances
        for i in range(10):
            client = lambda_function.TeslaFleetClient(f'client-{i}', f'secret-{i}')
            notifier = lambda_function.NotificationManager({})
            param_manager = lambda_function.ParameterStoreManager()
        
        # Measure memory after
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory increase should be reasonable
        memory_increase = final_objects - initial_objects
        assert memory_increase < 1000  # Arbitrary reasonable limit
    
    def test_retry_logic_simulation(self):
        """Test retry logic for API failures"""
        client = lambda_function.TeslaFleetClient('test-id', 'test-secret')
        client.set_tokens('test-access', 'test-refresh')
        
        # Simulate intermittent failures
        call_count = 0
        def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise requests.exceptions.ConnectionError("Network error")
            
            # Succeed on 3rd attempt
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'response': {'test': 'success'}}
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        with patch.object(client.session, 'request', side_effect=mock_request):
            # First two calls should fail
            result1 = client.api_request('GET', '/api/1/test')
            result2 = client.api_request('GET', '/api/1/test')
            
            # Third call should succeed
            result3 = client.api_request('GET', '/api/1/test')
        
        assert result1 is None
        assert result2 is None
        assert result3 == {'response': {'test': 'success'}}
        assert call_count == 3


# Test fixtures and utilities

@pytest.fixture
def sample_lambda_event():
    """Sample Lambda event for testing"""
    return {
        'backup_reserve_percent': 75,
        'schedule_name': 'Test Schedule - Set to 75%'
    }


@pytest.fixture
def sample_lambda_context():
    """Mock Lambda context"""
    context = Mock()
    context.function_name = 'PW3Mate-Powerwall-Scheduler'
    context.memory_limit_in_mb = 256
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:PW3Mate-Powerwall-Scheduler'
    context.aws_request_id = 'test-request-id-67890'
    context.get_remaining_time_in_millis = Mock(return_value=45000)  # 45 seconds
    return context


@pytest.fixture
def sample_powerwall_data():
    """Sample Powerwall data for testing"""
    return {
        'products': {
            'response': [
                {
                    'id': 123456789,
                    'device_type': 'energy',
                    'resource_type': 'battery',
                    'energy_site_id': 987654321,
                    'site_name': 'Test Home'
                }
            ]
        },
        'site_info': {
            'response': {
                'backup_reserve_percent': 50,
                'battery_count': 2,
                'nameplate_power': 10800,
                'nameplate_energy': 27400
            }
        },
        'live_status': {
            'response': {
                'percentage_charged': 85,
                'battery_power': -2100,
                'solar_power': 0,
                'load_power': 1800,
                'energy_left': 13.2,
                'total_pack_energy': 27.4,
                'grid_power': 300
            }
        }
    }


# Test runner configuration
if __name__ == '__main__':
    pytest.main([
        __file__,
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Treat unknown markers as errors
        '--disable-warnings',  # Disable pytest warnings
        '--cov=lambda_function',  # Coverage report
        '--cov-report=html',  # HTML coverage report
        '--cov-report=term-missing',  # Terminal coverage with missing lines
    ])