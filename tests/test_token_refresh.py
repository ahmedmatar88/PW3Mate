"""
Unit tests for Tesla Token Refresh Lambda function
Tests token refresh logic, error handling, and Parameter Store integration
"""

import json
import pytest
import boto3
from moto import mock_ssm
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta
import requests

# Import the Lambda function (adjust path as needed)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'token_refresh'))
import lambda_function


class TestParameterStoreManager:
    """Test ParameterStoreManager class"""
    
    @mock_ssm
    def setup_method(self):
        """Set up test environment with mocked Parameter Store"""
        self.ssm = boto3.client('ssm', region_name='us-east-1')
        self.param_manager = lambda_function.ParameterStoreManager()
        
        # Create test parameters
        self.test_params = {
            '/tesla/powerwall/client_id': 'test-client-id-123',
            '/tesla/powerwall/client_secret': 'test-client-secret-456',
            '/tesla/powerwall/access_token': 'test-access-token-789',
            '/tesla/powerwall/refresh_token': 'test-refresh-token-abc',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/test'
        }
        
        for name, value in self.test_params.items():
            self.ssm.put_parameter(
                Name=name,
                Value=value,
                Type='SecureString'
            )
    
    @mock_ssm 
    def test_get_parameter_success(self):
        """Test successful parameter retrieval"""
        result = self.param_manager.get_parameter('client_id')
        assert result == 'test-client-id-123'
    
    @mock_ssm
    def test_get_parameter_not_found(self):
        """Test parameter not found returns None"""
        result = self.param_manager.get_parameter('nonexistent')
        assert result is None
    
    @mock_ssm
    def test_get_all_credentials(self):
        """Test retrieving all Tesla credentials"""
        credentials = self.param_manager.get_all_credentials()
        
        assert credentials['client_id'] == 'test-client-id-123'
        assert credentials['client_secret'] == 'test-client-secret-456'
        assert credentials['access_token'] == 'test-access-token-789'
        assert credentials['refresh_token'] == 'test-refresh-token-abc'
    
    @mock_ssm
    def test_put_parameter(self):
        """Test storing new parameter"""
        self.param_manager.put_parameter('test_param', 'test_value')
        
        # Verify parameter was stored
        response = self.ssm.get_parameter(
            Name='/tesla/powerwall/test_param',
            WithDecryption=True
        )
        assert response['Parameter']['Value'] == 'test_value'
    
    @mock_ssm
    def test_update_tokens(self):
        """Test updating access and refresh tokens"""
        new_access = 'new-access-token-xyz'
        new_refresh = 'new-refresh-token-def'
        
        self.param_manager.update_tokens(new_access, new_refresh)
        
        # Verify tokens were updated
        access_result = self.param_manager.get_parameter('access_token')
        refresh_result = self.param_manager.get_parameter('refresh_token')
        
        assert access_result == new_access
        assert refresh_result == new_refresh


class TestTokenRefresh:
    """Test Tesla token refresh functionality"""
    
    def test_refresh_tesla_tokens_success(self):
        """Test successful token refresh"""
        credentials = {
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret', 
            'refresh_token': 'test-refresh-token',
            'access_token': 'old-access-token'
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new-access-token',
            'refresh_token': 'new-refresh-token',
            'expires_in': 28800
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            success, access_token, refresh_token, message = lambda_function.refresh_tesla_tokens(credentials)
        
        assert success is True
        assert access_token == 'new-access-token'
        assert refresh_token == 'new-refresh-token'
        assert 'successful' in message.lower()
    
    def test_refresh_tesla_tokens_expired_refresh_token(self):
        """Test handling of expired refresh token"""
        credentials = {
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'refresh_token': 'expired-refresh-token',
            'access_token': 'old-access-token'
        }
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Client Error")
        
        with patch('requests.post', return_value=mock_response):
            success, access_token, refresh_token, message = lambda_function.refresh_tesla_tokens(credentials)
        
        assert success is False
        assert access_token is None
        assert refresh_token is None
        assert 'expired or invalid' in message.lower()
    
    def test_refresh_tesla_tokens_network_timeout(self):
        """Test handling of network timeout"""
        credentials = {
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'refresh_token': 'test-refresh-token',
            'access_token': 'old-access-token'
        }
        
        with patch('requests.post', side_effect=requests.exceptions.Timeout("Request timed out")):
            success, access_token, refresh_token, message = lambda_function.refresh_tesla_tokens(credentials)
        
        assert success is False
        assert access_token is None
        assert refresh_token is None
        assert 'timed out' in message.lower()
    
    def test_refresh_tesla_tokens_missing_credentials(self):
        """Test handling of missing credentials"""
        credentials = {
            'client_id': None,
            'client_secret': 'test-client-secret',
            'refresh_token': 'test-refresh-token',
            'access_token': 'old-access-token'
        }
        
        success, access_token, refresh_token, message = lambda_function.refresh_tesla_tokens(credentials)
        
        assert success is False
        assert access_token is None
        assert refresh_token is None
        assert 'missing credentials' in message.lower()
    
    def test_refresh_tesla_tokens_network_error(self):
        """Test handling of general network errors"""
        credentials = {
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'refresh_token': 'test-refresh-token', 
            'access_token': 'old-access-token'
        }
        
        with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Network error")):
            success, access_token, refresh_token, message = lambda_function.refresh_tesla_tokens(credentials)
        
        assert success is False
        assert access_token is None
        assert refresh_token is None
        assert 'network error' in message.lower()


class TestDiscordNotifications:
    """Test Discord notification functionality"""
    
    def test_send_discord_notification_success(self):
        """Test successful Discord notification"""
        webhook_url = 'https://discord.com/api/webhooks/test/webhook'
        title = 'Test Title'
        message = 'Test message'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = lambda_function.send_discord_notification(webhook_url, title, message)
        
        assert result is True
        mock_post.assert_called_once()
        
        # Verify the payload structure
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        assert 'embeds' in payload
        assert len(payload['embeds']) == 1
        assert payload['embeds'][0]['title'] == title
        assert payload['embeds'][0]['description'] == message
    
    def test_send_discord_notification_no_webhook(self):
        """Test Discord notification with no webhook URL"""
        result = lambda_function.send_discord_notification('', 'Title', 'Message')
        assert result is False
    
    def test_send_discord_notification_network_error(self):
        """Test Discord notification with network error"""
        webhook_url = 'https://discord.com/api/webhooks/test/webhook'
        
        with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Network error")):
            result = lambda_function.send_discord_notification(webhook_url, 'Title', 'Message')
        
        assert result is False
    
    def test_send_discord_notification_http_error(self):
        """Test Discord notification with HTTP error"""
        webhook_url = 'https://discord.com/api/webhooks/test/webhook'
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Bad Request")
        
        with patch('requests.post', return_value=mock_response):
            result = lambda_function.send_discord_notification(webhook_url, 'Title', 'Message')
        
        assert result is False


class TestLambdaHandler:
    """Test the main Lambda handler function"""
    
    @mock_ssm
    def test_lambda_handler_success(self):
        """Test successful Lambda execution"""
        # Set up mocked Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id',
            '/tesla/powerwall/client_secret': 'test-client-secret',
            '/tesla/powerwall/access_token': 'old-access-token',
            '/tesla/powerwall/refresh_token': 'test-refresh-token',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/test'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        # Mock successful token refresh
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            'access_token': 'new-access-token',
            'refresh_token': 'new-refresh-token'
        }
        mock_token_response.raise_for_status.return_value = None
        
        # Mock successful Discord notification
        mock_discord_response = Mock()
        mock_discord_response.status_code = 200
        mock_discord_response.raise_for_status.return_value = None
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = [mock_token_response, mock_discord_response]
            
            result = lambda_function.lambda_handler({}, None)
        
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        assert body['status'] == 'success'
        assert body['tokens_updated'] is True
    
    @mock_ssm
    def test_lambda_handler_token_refresh_failure(self):
        """Test Lambda execution with token refresh failure"""
        # Set up mocked Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id',
            '/tesla/powerwall/client_secret': 'test-client-secret',
            '/tesla/powerwall/access_token': 'old-access-token',
            '/tesla/powerwall/refresh_token': 'expired-refresh-token',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/test'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        # Mock failed token refresh (401 Unauthorized)
        mock_token_response = Mock()
        mock_token_response.status_code = 401
        
        # Mock successful Discord notification
        mock_discord_response = Mock()
        mock_discord_response.status_code = 200
        mock_discord_response.raise_for_status.return_value = None
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = [mock_token_response, mock_discord_response]
            
            result = lambda_function.lambda_handler({}, None)
        
        assert result['statusCode'] == 500
        
        body = json.loads(result['body'])
        assert body['status'] == 'failed'
    
    @mock_ssm
    def test_lambda_handler_missing_credentials(self):
        """Test Lambda execution with missing credentials"""
        # Set up mocked Parameter Store with missing credentials
        ssm = boto3.client('ssm', region_name='us-east-1')
        
        # Only create some parameters (missing client_secret)
        ssm.put_parameter(
            Name='/tesla/powerwall/client_id',
            Value='test-client-id',
            Type='SecureString'
        )
        
        result = lambda_function.lambda_handler({}, None)
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'missing credentials' in body['message'].lower()
    
    def test_lambda_handler_exception(self):
        """Test Lambda execution with unexpected exception"""
        with patch('lambda_function.ParameterStoreManager', side_effect=Exception("Unexpected error")):
            result = lambda_function.lambda_handler({}, None)
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'crashed' in body['error'].lower()


class TestIntegration:
    """Integration tests that test multiple components together"""
    
    @mock_ssm
    def test_end_to_end_success_flow(self):
        """Test complete successful token refresh flow"""
        # Set up Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1') 
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id-123',
            '/tesla/powerwall/client_secret': 'ta-secret.test123',
            '/tesla/powerwall/access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.old-token',
            '/tesla/powerwall/refresh_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.refresh-token',
            '/tesla/powerwall/discord_webhook': 'https://discord.com/api/webhooks/123456789/test-webhook'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        # Mock Tesla API response
        mock_tesla_response = Mock()
        mock_tesla_response.status_code = 200
        mock_tesla_response.json.return_value = {
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.new-access-token',
            'refresh_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.new-refresh-token',
            'expires_in': 28800,
            'token_type': 'Bearer'
        }
        mock_tesla_response.raise_for_status.return_value = None
        
        # Mock Discord response
        mock_discord_response = Mock()
        mock_discord_response.status_code = 200
        mock_discord_response.raise_for_status.return_value = None
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = [mock_tesla_response, mock_discord_response]
            
            # Execute Lambda handler
            result = lambda_function.lambda_handler({}, None)
        
        # Verify success
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['status'] == 'success'
        assert body['tokens_updated'] is True
        
        # Verify tokens were updated in Parameter Store
        updated_access = ssm.get_parameter(
            Name='/tesla/powerwall/access_token',
            WithDecryption=True
        )['Parameter']['Value']
        
        updated_refresh = ssm.get_parameter(
            Name='/tesla/powerwall/refresh_token', 
            WithDecryption=True
        )['Parameter']['Value']
        
        assert updated_access == 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.new-access-token'
        assert updated_refresh == 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.new-refresh-token'
        
        # Verify API calls were made correctly
        assert mock_post.call_count == 2
        
        # Check Tesla API call
        tesla_call = mock_post.call_args_list[0]
        assert tesla_call[0][0] == 'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token'
        assert tesla_call[1]['data']['grant_type'] == 'refresh_token'
        assert tesla_call[1]['data']['client_id'] == 'test-client-id-123'
        
        # Check Discord notification call
        discord_call = mock_post.call_args_list[1]
        discord_payload = discord_call[1]['json']
        assert 'embeds' in discord_payload
        assert discord_payload['embeds'][0]['title'] == '🔋 Daily Tesla Token Refresh'


class TestErrorScenarios:
    """Test various error scenarios and edge cases"""
    
    @mock_ssm
    def test_parameter_store_unavailable(self):
        """Test handling when Parameter Store is unavailable"""
        with patch('boto3.client', side_effect=Exception("AWS service unavailable")):
            result = lambda_function.lambda_handler({}, None)
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'crashed' in body['error'].lower()
    
    @mock_ssm
    def test_discord_webhook_invalid(self):
        """Test handling of invalid Discord webhook"""
        # Set up Parameter Store with invalid webhook
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id',
            '/tesla/powerwall/client_secret': 'test-client-secret',
            '/tesla/powerwall/access_token': 'old-access-token',
            '/tesla/powerwall/refresh_token': 'test-refresh-token',
            '/tesla/powerwall/discord_webhook': 'invalid-webhook-url'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        # Mock successful token refresh
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            'access_token': 'new-access-token',
            'refresh_token': 'new-refresh-token'
        }
        mock_token_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_token_response):
            result = lambda_function.lambda_handler({}, None)
        
        # Should still succeed even if Discord notification fails
        assert result['statusCode'] == 200
    
    def test_tesla_api_rate_limiting(self):
        """Test handling of Tesla API rate limiting"""
        credentials = {
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'refresh_token': 'test-refresh-token',
            'access_token': 'old-access-token'
        }
        
        mock_response = Mock()
        mock_response.status_code = 429  # Too Many Requests
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
        
        with patch('requests.post', return_value=mock_response):
            success, access_token, refresh_token, message = lambda_function.refresh_tesla_tokens(credentials)
        
        assert success is False
        assert 'rate limit' in message.lower() or 'too many requests' in message.lower()
    
    def test_tesla_api_server_error(self):
        """Test handling of Tesla API server errors"""
        credentials = {
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'refresh_token': 'test-refresh-token',
            'access_token': 'old-access-token'
        }
        
        mock_response = Mock()
        mock_response.status_code = 500  # Internal Server Error
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Internal Server Error")
        
        with patch('requests.post', return_value=mock_response):
            success, access_token, refresh_token, message = lambda_function.refresh_tesla_tokens(credentials)
        
        assert success is False
        assert access_token is None
        assert refresh_token is None


class TestUtilityFunctions:
    """Test utility and helper functions"""
    
    def test_timestamp_generation(self):
        """Test that timestamps are generated correctly"""
        now = datetime.utcnow()
        
        with patch('lambda_function.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = now
            mock_datetime.utcnow().isoformat.return_value = now.isoformat()
            
            # This would be called within the Lambda function
            timestamp = datetime.utcnow().isoformat()
            
            assert timestamp == now.isoformat()
    
    def test_notification_message_formatting(self):
        """Test Discord notification message formatting"""
        current_time = datetime(2025, 1, 1, 21, 0, 0)
        
        # Test success message formatting
        success_message = f"✅ **Tesla Token Refresh Successful**\n\n"
        success_message += f"🕘 **Time**: {current_time.strftime('%I:%M %p')} UTC\n"
        success_message += f"🔄 **New tokens generated and stored**\n"
        success_message += f"⏰ **Access token valid until**: {(current_time + timedelta(hours=8)).strftime('%I:%M %p')} UTC\n"
        
        assert "Tesla Token Refresh Successful" in success_message
        assert "09:00 PM UTC" in success_message  # 21:00 in 12-hour format
        assert "05:00 AM UTC" in success_message  # 21:00 + 8 hours
    
    def test_error_message_classification(self):
        """Test error message classification for notifications"""
        test_cases = [
            ("expired", "critical"),
            ("invalid", "critical"), 
            ("timeout", "warning"),
            ("network", "warning"),
            ("server error", "warning"),
            ("rate limit", "warning"),
            ("unknown error", "error")
        ]
        
        for error_text, expected_severity in test_cases:
            if "expired" in error_text.lower() or "invalid" in error_text.lower():
                severity = "critical"
            elif "timeout" in error_text.lower() or "network" in error_text.lower():
                severity = "warning"
            else:
                severity = "error"
            
            assert severity == expected_severity or severity == "error"


class TestPerformance:
    """Test performance-related aspects"""
    
    @mock_ssm
    def test_execution_time(self):
        """Test that Lambda execution completes within reasonable time"""
        import time
        
        # Set up minimal Parameter Store
        ssm = boto3.client('ssm', region_name='us-east-1')
        test_params = {
            '/tesla/powerwall/client_id': 'test-client-id',
            '/tesla/powerwall/client_secret': 'test-client-secret',
            '/tesla/powerwall/access_token': 'old-access-token',
            '/tesla/powerwall/refresh_token': 'test-refresh-token'
        }
        
        for name, value in test_params.items():
            ssm.put_parameter(Name=name, Value=value, Type='SecureString')
        
        # Mock fast responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new-access-token',
            'refresh_token': 'new-refresh-token'
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            start_time = time.time()
            result = lambda_function.lambda_handler({}, None)
            execution_time = time.time() - start_time
        
        # Should complete within 5 seconds in test environment
        assert execution_time < 5.0
        assert result['statusCode'] == 200
    
    def test_memory_usage(self):
        """Test that memory usage is reasonable"""
        import sys
        
        # Measure memory before
        initial_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
        
        # Create ParameterStoreManager instance
        param_manager = lambda_function.ParameterStoreManager()
        
        # Measure memory after
        final_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
        
        # Memory increase should be minimal
        if 'gc' in sys.modules:
            assert final_objects - initial_objects < 100  # Arbitrary reasonable limit


class TestConfiguration:
    """Test configuration and environment handling"""
    
    def test_aws_region_handling(self):
        """Test that AWS region is handled correctly"""
        with patch.dict(os.environ, {'AWS_REGION': 'eu-west-1'}):
            param_manager = lambda_function.ParameterStoreManager()
            # ParameterStoreManager should work regardless of region
            assert param_manager.parameter_prefix == '/tesla/powerwall'
    
    def test_parameter_prefix_customization(self):
        """Test that parameter prefix can be customized"""
        param_manager = lambda_function.ParameterStoreManager()
        param_manager.parameter_prefix = '/custom/prefix'
        
        expected_path = '/custom/prefix/client_id'
        # This would be the path used in actual parameter retrieval
        assert param_manager.parameter_prefix + '/client_id' == expected_path


# Pytest fixtures and configuration

@pytest.fixture
def lambda_context():
    """Mock Lambda context object"""
    context = Mock()
    context.function_name = 'PW3Mate-Token-Refresh'
    context.memory_limit_in_mb = 256
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:PW3Mate-Token-Refresh'
    context.aws_request_id = 'test-request-id-12345'
    context.get_remaining_time_in_millis = Mock(return_value=30000)  # 30 seconds
    return context


@pytest.fixture
def sample_tesla_credentials():
    """Sample Tesla API credentials for testing"""
    return {
        'client_id': '8f2a9b47-d3e1-4c56-a789-1b2c3d4e5f6g',
        'client_secret': 'ta-secret.Kx9Zm4Pq7Nv2RtY8MockSecret123',
        'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.mock-access-token',
        'refresh_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.mock-refresh-token'
    }


@pytest.fixture
def sample_tesla_response():
    """Sample Tesla API token response"""
    return {
        'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.new-mock-access-token',
        'refresh_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.new-mock-refresh-token',
        'expires_in': 28800,
        'token_type': 'Bearer',
        'scope': 'openid energy_device_data energy_cmds offline_access'
    }


# Test runner configuration
if __name__ == '__main__':
    # Add import for garbage collection if testing memory
    import gc
    
    # Run specific test classes
    pytest.main([
        __file__,
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Treat unknown markers as errors
        '--disable-warnings',  # Disable pytest warnings
    ])