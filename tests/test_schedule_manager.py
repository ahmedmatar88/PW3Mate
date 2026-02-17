"""
Tests for PW3Mate Schedule Manager Lambda
"""

import json
import time
import pytest
from unittest.mock import patch, MagicMock
try:
    from moto import mock_aws_ssm as mock_aws_ssm
except ImportError:
    from moto import mock_aws as mock_aws_ssm
import boto3

# Import the module under test
import sys
import os

os.environ.setdefault('AWS_DEFAULT_REGION', 'eu-west-1')
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'testing')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'testing')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'schedule_manager'))
import lambda_function


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def lambda_context():
    ctx = MagicMock()
    ctx.function_name = 'PW3Mate-Schedule-Manager'
    ctx.memory_limit_in_mb = 256
    ctx.invoked_function_arn = 'arn:aws:lambda:eu-west-1:123456789012:function:PW3Mate-Schedule-Manager'
    ctx.aws_request_id = 'test-request-id'
    return ctx


@pytest.fixture
def api_event():
    """Factory for API Gateway proxy events."""
    def _make(method, path, body=None, token=None):
        event = {
            'httpMethod': method,
            'path': path,
            'headers': {},
            'body': json.dumps(body) if body else None,
        }
        if token:
            event['headers']['Authorization'] = f'Bearer {token}'
        return event
    return _make


@pytest.fixture
def ssm_setup():
    """Set up Parameter Store with a known UI password."""
    with mock_aws_ssm():
        ssm = boto3.client('ssm', region_name='eu-west-1')
        ssm.put_parameter(
            Name='/tesla/powerwall/ui_password',
            Value='testpassword123',
            Type='SecureString',
        )
        yield ssm


# ---------------------------------------------------------------------------
#  Auth – generate_token / validate_token
# ---------------------------------------------------------------------------

class TestAuth:

    def test_generate_and_validate_token(self):
        token = lambda_function.generate_token('pw')
        assert isinstance(token, str)
        assert '.' in token

        with patch.object(lambda_function, 'get_parameter', return_value='pw'):
            assert lambda_function.validate_token(token) is True

    def test_validate_token_bad_signature(self):
        token = lambda_function.generate_token('pw')
        parts = token.split('.')
        bad_token = parts[0] + '.badsignature'

        with patch.object(lambda_function, 'get_parameter', return_value='pw'):
            assert lambda_function.validate_token(bad_token) is False

    def test_validate_token_expired(self):
        with patch('lambda_function.time') as mock_time:
            mock_time.time.return_value = 1000000
            token = lambda_function.generate_token('pw')

        with patch.object(lambda_function, 'get_parameter', return_value='pw'):
            assert lambda_function.validate_token(token) is False

    def test_validate_token_no_password_in_store(self):
        with patch.object(lambda_function, 'get_parameter', return_value=None):
            assert lambda_function.validate_token('anything.here') is False

    def test_validate_token_malformed(self):
        with patch.object(lambda_function, 'get_parameter', return_value='pw'):
            assert lambda_function.validate_token('nodotshere') is False
            assert lambda_function.validate_token('') is False


# ---------------------------------------------------------------------------
#  Login handler
# ---------------------------------------------------------------------------

class TestLogin:

    def test_login_success(self, api_event, lambda_context):
        with patch.object(lambda_function, 'get_parameter', return_value='testpassword123'):
            event = api_event('POST', '/api/login', body={'password': 'testpassword123'})
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'token' in body

    def test_login_wrong_password(self, api_event, lambda_context):
        with patch.object(lambda_function, 'get_parameter', return_value='correct'):
            event = api_event('POST', '/api/login', body={'password': 'wrong'})
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 401

    def test_login_no_password_configured(self, api_event, lambda_context):
        with patch.object(lambda_function, 'get_parameter', return_value=None):
            event = api_event('POST', '/api/login', body={'password': 'anything'})
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 500


# ---------------------------------------------------------------------------
#  CORS
# ---------------------------------------------------------------------------

class TestCORS:

    def test_options_returns_cors_headers(self, lambda_context):
        event = {'httpMethod': 'OPTIONS', 'path': '/api/schedules', 'headers': {}}
        result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 200
        assert result['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'Authorization' in result['headers']['Access-Control-Allow-Headers']

    def test_all_responses_have_cors(self, api_event, lambda_context):
        event = api_event('GET', '/api/schedules')  # no auth → 401
        with patch.object(lambda_function, 'validate_token', return_value=False):
            result = lambda_function.lambda_handler(event, lambda_context)

        assert 'Access-Control-Allow-Origin' in result['headers']


# ---------------------------------------------------------------------------
#  Unauthorised access
# ---------------------------------------------------------------------------

class TestUnauthorised:

    def test_no_token(self, api_event, lambda_context):
        event = api_event('GET', '/api/schedules')
        with patch.object(lambda_function, 'validate_token', return_value=False):
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 401

    def test_invalid_token(self, api_event, lambda_context):
        event = api_event('GET', '/api/schedules', token='bad.token')
        with patch.object(lambda_function, 'validate_token', return_value=False):
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 401


# ---------------------------------------------------------------------------
#  list_schedules
# ---------------------------------------------------------------------------

class TestListSchedules:

    def test_list_schedules_success(self, api_event, lambda_context):
        mock_events = MagicMock()
        mock_events.list_rules.return_value = {
            'Rules': [
                {
                    'Name': 'PW3Mate-Powerwall-2331-100percent',
                    'ScheduleExpression': 'cron(31 23 * * ? *)',
                    'State': 'ENABLED',
                },
                {
                    'Name': 'PW3Mate-Powerwall-0529-0percent',
                    'ScheduleExpression': 'cron(29 5 * * ? *)',
                    'State': 'ENABLED',
                },
            ]
        }
        mock_events.list_targets_by_rule.side_effect = [
            {'Targets': [{'Input': json.dumps({'backup_reserve_percent': 100, 'schedule_name': '11:31 PM'})}]},
            {'Targets': [{'Input': json.dumps({'backup_reserve_percent': 0, 'schedule_name': '5:29 AM'})}]},
        ]

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto:
            mock_boto.client.return_value = mock_events
            event = api_event('GET', '/api/schedules', token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert len(body['schedules']) == 2
        # Should be sorted by time
        assert body['schedules'][0]['hour'] == 5
        assert body['schedules'][1]['hour'] == 23

    def test_list_filters_token_refresh_rules(self, api_event, lambda_context):
        mock_events = MagicMock()
        mock_events.list_rules.return_value = {
            'Rules': [
                {'Name': 'PW3Mate-Powerwall-Token-Refresh-9PM', 'ScheduleExpression': 'cron(0 21 * * ? *)', 'State': 'ENABLED'},
                {'Name': 'PW3Mate-Powerwall-2331-100percent', 'ScheduleExpression': 'cron(31 23 * * ? *)', 'State': 'ENABLED'},
            ]
        }
        mock_events.list_targets_by_rule.return_value = {
            'Targets': [{'Input': json.dumps({'backup_reserve_percent': 100, 'schedule_name': 'test'})}]
        }

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto:
            mock_boto.client.return_value = mock_events
            event = api_event('GET', '/api/schedules', token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        body = json.loads(result['body'])
        assert len(body['schedules']) == 1
        assert 'Token-Refresh' not in body['schedules'][0]['rule_name']

    def test_list_empty(self, api_event, lambda_context):
        mock_events = MagicMock()
        mock_events.list_rules.return_value = {'Rules': []}

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto:
            mock_boto.client.return_value = mock_events
            event = api_event('GET', '/api/schedules', token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        body = json.loads(result['body'])
        assert body['schedules'] == []


# ---------------------------------------------------------------------------
#  create_schedule
# ---------------------------------------------------------------------------

class TestCreateSchedule:

    @patch.dict(os.environ, {'SCHEDULER_LAMBDA_ARN': 'arn:aws:lambda:eu-west-1:123:function:PW3Mate-Powerwall-Scheduler'})
    def test_create_success(self, api_event, lambda_context):
        mock_events = MagicMock()

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto, \
             patch.object(lambda_function, 'SCHEDULER_LAMBDA_ARN', 'arn:aws:lambda:eu-west-1:123:function:PW3Mate-Powerwall-Scheduler'):
            mock_boto.client.return_value = mock_events
            event = api_event('POST', '/api/schedules', body={'hour': 14, 'minute': 30, 'percentage': 80}, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 201
        body = json.loads(result['body'])
        assert body['rule_name'] == 'PW3Mate-Powerwall-1430-80percent'

        mock_events.put_rule.assert_called_once()
        call_kwargs = mock_events.put_rule.call_args[1]
        assert call_kwargs['ScheduleExpression'] == 'cron(30 14 * * ? *)'
        assert call_kwargs['State'] == 'ENABLED'

        mock_events.put_targets.assert_called_once()

    def test_create_missing_fields(self, api_event, lambda_context):
        with patch.object(lambda_function, 'validate_token', return_value=True):
            event = api_event('POST', '/api/schedules', body={'hour': 10}, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 400

    def test_create_invalid_time(self, api_event, lambda_context):
        with patch.object(lambda_function, 'validate_token', return_value=True):
            event = api_event('POST', '/api/schedules', body={'hour': 25, 'minute': 0, 'percentage': 50}, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 400

    def test_create_invalid_percentage(self, api_event, lambda_context):
        with patch.object(lambda_function, 'validate_token', return_value=True):
            event = api_event('POST', '/api/schedules', body={'hour': 10, 'minute': 0, 'percentage': 150}, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 400

    def test_create_no_lambda_arn(self, api_event, lambda_context):
        mock_events = MagicMock()

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto, \
             patch.object(lambda_function, 'SCHEDULER_LAMBDA_ARN', ''):
            mock_boto.client.return_value = mock_events
            event = api_event('POST', '/api/schedules', body={'hour': 10, 'minute': 0, 'percentage': 50}, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 500


# ---------------------------------------------------------------------------
#  update_schedule
# ---------------------------------------------------------------------------

class TestUpdateSchedule:

    def test_toggle_enable(self, api_event, lambda_context):
        mock_events = MagicMock()

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto:
            mock_boto.client.return_value = mock_events
            event = api_event('PUT', '/api/schedules', body={
                'rule_name': 'PW3Mate-Powerwall-2331-100percent',
                'enabled': False,
            }, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 200
        mock_events.disable_rule.assert_called_once_with(Name='PW3Mate-Powerwall-2331-100percent')

    def test_toggle_disable(self, api_event, lambda_context):
        mock_events = MagicMock()

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto:
            mock_boto.client.return_value = mock_events
            event = api_event('PUT', '/api/schedules', body={
                'rule_name': 'PW3Mate-Powerwall-2331-100percent',
                'enabled': True,
            }, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 200
        mock_events.enable_rule.assert_called_once()

    def test_full_update_same_name(self, api_event, lambda_context):
        mock_events = MagicMock()

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto, \
             patch.object(lambda_function, 'SCHEDULER_LAMBDA_ARN', 'arn:test'):
            mock_boto.client.return_value = mock_events
            event = api_event('PUT', '/api/schedules', body={
                'rule_name': 'PW3Mate-Powerwall-2331-100percent',
                'hour': 23, 'minute': 31, 'percentage': 100,
            }, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 200
        # Should NOT delete old rule since name is the same
        mock_events.delete_rule.assert_not_called()

    def test_full_update_name_changes(self, api_event, lambda_context):
        mock_events = MagicMock()

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto, \
             patch.object(lambda_function, 'SCHEDULER_LAMBDA_ARN', 'arn:test'):
            mock_boto.client.return_value = mock_events
            event = api_event('PUT', '/api/schedules', body={
                'rule_name': 'PW3Mate-Powerwall-2331-100percent',
                'hour': 22, 'minute': 0, 'percentage': 80,
            }, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['rule_name'] == 'PW3Mate-Powerwall-2200-80percent'
        # Old rule should be deleted
        mock_events.remove_targets.assert_called_once()
        mock_events.delete_rule.assert_called_once_with(Name='PW3Mate-Powerwall-2331-100percent')

    def test_update_missing_rule_name(self, api_event, lambda_context):
        with patch.object(lambda_function, 'validate_token', return_value=True):
            event = api_event('PUT', '/api/schedules', body={'hour': 10, 'minute': 0, 'percentage': 50}, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 400

    def test_update_rejects_non_pw3mate_rule(self, api_event, lambda_context):
        with patch.object(lambda_function, 'validate_token', return_value=True):
            event = api_event('PUT', '/api/schedules', body={
                'rule_name': 'SomeOtherRule',
                'enabled': False,
            }, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 403


# ---------------------------------------------------------------------------
#  delete_schedule
# ---------------------------------------------------------------------------

class TestDeleteSchedule:

    def test_delete_success(self, api_event, lambda_context):
        mock_events = MagicMock()

        with patch.object(lambda_function, 'validate_token', return_value=True), \
             patch('lambda_function.boto3') as mock_boto:
            mock_boto.client.return_value = mock_events
            event = api_event('DELETE', '/api/schedules', body={
                'rule_name': 'PW3Mate-Powerwall-2331-100percent',
            }, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)

        assert result['statusCode'] == 200
        mock_events.remove_targets.assert_called_once()
        mock_events.delete_rule.assert_called_once()

    def test_delete_missing_name(self, api_event, lambda_context):
        with patch.object(lambda_function, 'validate_token', return_value=True):
            event = api_event('DELETE', '/api/schedules', body={}, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 400

    def test_delete_rejects_non_pw3mate_rule(self, api_event, lambda_context):
        with patch.object(lambda_function, 'validate_token', return_value=True):
            event = api_event('DELETE', '/api/schedules', body={'rule_name': 'NotPW3Mate'}, token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 403


# ---------------------------------------------------------------------------
#  Routing
# ---------------------------------------------------------------------------

class TestRouting:

    def test_unknown_path(self, api_event, lambda_context):
        with patch.object(lambda_function, 'validate_token', return_value=True):
            event = api_event('GET', '/api/unknown', token='valid')
            result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 404

    def test_invalid_json_body(self, lambda_context):
        event = {
            'httpMethod': 'POST',
            'path': '/api/login',
            'headers': {},
            'body': 'not json',
        }
        result = lambda_function.lambda_handler(event, lambda_context)
        assert result['statusCode'] == 400


# ---------------------------------------------------------------------------
#  Helper functions
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_parse_cron(self):
        assert lambda_function.parse_cron('cron(31 23 * * ? *)') == (23, 31)
        assert lambda_function.parse_cron('cron(0 5 * * ? *)') == (5, 0)
        assert lambda_function.parse_cron('rate(1 hour)') == (None, None)

    def test_build_rule_name(self):
        assert lambda_function.build_rule_name(23, 31, 100) == 'PW3Mate-Powerwall-2331-100percent'
        assert lambda_function.build_rule_name(0, 5, 0) == 'PW3Mate-Powerwall-0005-0percent'

    def test_build_schedule_name(self):
        name = lambda_function.build_schedule_name(23, 31, 100)
        assert '11:31 PM UTC' in name
        assert '100%' in name

        name2 = lambda_function.build_schedule_name(0, 0, 0)
        assert '12:00 AM UTC' in name2

    def test_cors_response_structure(self):
        resp = lambda_function.cors_response(200, {'ok': True})
        assert resp['statusCode'] == 200
        assert resp['headers']['Content-Type'] == 'application/json'
        assert resp['headers']['Access-Control-Allow-Origin'] == '*'
        body = json.loads(resp['body'])
        assert body['ok'] is True
