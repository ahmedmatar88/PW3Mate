"""
PW3Mate Schedule Manager API
Manages EventBridge rules for Powerwall backup reserve scheduling.
Provides REST API behind API Gateway for the web UI.
"""

import json
import os
import re
import hmac
import hashlib
import base64
import time
import boto3
import logging
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
SCHEDULER_LAMBDA_ARN = os.environ.get('SCHEDULER_LAMBDA_ARN', '')
RULE_PREFIX = 'PW3Mate-Powerwall-'
TOKEN_EXPIRY_HOURS = 24


# ---------------------------------------------------------------------------
# Parameter Store
# ---------------------------------------------------------------------------

def get_parameter(name: str) -> Optional[str]:
    """Get a parameter from AWS Systems Manager Parameter Store."""
    ssm = boto3.client('ssm')
    try:
        response = ssm.get_parameter(
            Name=f'/tesla/powerwall/{name}',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Failed to get parameter {name}: {e}")
        return None


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def generate_token(password: str) -> str:
    """Generate an HMAC-signed auth token with an expiry claim."""
    payload = json.dumps({
        'exp': int(time.time()) + (TOKEN_EXPIRY_HOURS * 3600),
        'iat': int(time.time())
    })
    encoded_payload = base64.urlsafe_b64encode(payload.encode()).decode()
    signature = hmac.new(
        password.encode(),
        encoded_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def validate_token(token: str) -> bool:
    """Validate an HMAC-signed auth token."""
    password = get_parameter('ui_password')
    if not password:
        return False

    try:
        parts = token.split('.')
        if len(parts) != 2:
            return False

        encoded_payload, signature = parts

        expected_sig = hmac.new(
            password.encode(),
            encoded_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return False

        payload = json.loads(base64.urlsafe_b64decode(encoded_payload))
        if payload.get('exp', 0) < time.time():
            return False

        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Response helper
# ---------------------------------------------------------------------------

def cors_response(status_code: int, body: dict) -> dict:
    """Build an API Gateway response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }


# ---------------------------------------------------------------------------
# Auth handler
# ---------------------------------------------------------------------------

def handle_login(body: dict) -> dict:
    """Authenticate with a simple password and return a signed token."""
    password = body.get('password', '')
    stored_password = get_parameter('ui_password')

    if not stored_password:
        return cors_response(500, {'error': 'UI password not configured in Parameter Store'})

    if not hmac.compare_digest(password, stored_password):
        return cors_response(401, {'error': 'Invalid password'})

    token = generate_token(stored_password)
    return cors_response(200, {'token': token})


# ---------------------------------------------------------------------------
# EventBridge helpers
# ---------------------------------------------------------------------------

def parse_cron(cron_expr: str) -> tuple:
    """Parse an EventBridge cron expression and return (hour, minute)."""
    match = re.match(r'cron\((\d+)\s+(\d+)\s+', cron_expr)
    if match:
        return int(match.group(2)), int(match.group(1))
    return None, None


def build_rule_name(hour: int, minute: int, percentage: int) -> str:
    """Build a deterministic EventBridge rule name."""
    return f"{RULE_PREFIX}{hour:02d}{minute:02d}-{percentage}percent"


def build_schedule_name(hour: int, minute: int, percentage: int) -> str:
    """Build a human-readable schedule label."""
    hour_12 = hour % 12 or 12
    am_pm = 'AM' if hour < 12 else 'PM'
    return f"{hour_12}:{minute:02d} {am_pm} UTC - Set to {percentage}%"


# ---------------------------------------------------------------------------
# CRUD handlers
# ---------------------------------------------------------------------------

def list_schedules() -> dict:
    """List all PW3Mate Powerwall EventBridge schedule rules."""
    events = boto3.client('events')

    try:
        response = events.list_rules(NamePrefix=RULE_PREFIX)
        rules = response.get('Rules', [])

        schedules = []
        for rule in rules:
            if 'Token-Refresh' in rule['Name']:
                continue

            schedule_expr = rule.get('ScheduleExpression', '')
            hour, minute = parse_cron(schedule_expr)

            targets_response = events.list_targets_by_rule(Rule=rule['Name'])
            targets = targets_response.get('Targets', [])

            percentage = None
            schedule_name = ''
            if targets:
                try:
                    input_json = json.loads(targets[0].get('Input', '{}'))
                    percentage = input_json.get('backup_reserve_percent')
                    schedule_name = input_json.get('schedule_name', '')
                except (json.JSONDecodeError, IndexError):
                    pass

            schedules.append({
                'rule_name': rule['Name'],
                'hour': hour,
                'minute': minute,
                'percentage': percentage,
                'schedule_name': schedule_name,
                'enabled': rule.get('State') == 'ENABLED',
                'cron': schedule_expr
            })

        schedules.sort(key=lambda s: (s['hour'] or 0, s['minute'] or 0))
        return cors_response(200, {'schedules': schedules})

    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        return cors_response(500, {'error': str(e)})


def create_schedule(body: dict) -> dict:
    """Create a new EventBridge schedule rule."""
    hour = body.get('hour')
    minute = body.get('minute')
    percentage = body.get('percentage')

    if hour is None or minute is None or percentage is None:
        return cors_response(400, {'error': 'hour, minute, and percentage are required'})

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return cors_response(400, {'error': 'Invalid time values'})

    if not (0 <= percentage <= 100):
        return cors_response(400, {'error': 'Percentage must be between 0 and 100'})

    rule_name = build_rule_name(hour, minute, percentage)
    schedule_name = build_schedule_name(hour, minute, percentage)

    events = boto3.client('events')

    try:
        events.put_rule(
            Name=rule_name,
            ScheduleExpression=f'cron({minute} {hour} * * ? *)',
            State='ENABLED',
            Description=f'PW3Mate: Set Powerwall backup reserve to {percentage}% at {hour:02d}:{minute:02d} UTC'
        )

        if not SCHEDULER_LAMBDA_ARN:
            return cors_response(500, {'error': 'SCHEDULER_LAMBDA_ARN environment variable not configured'})

        events.put_targets(
            Rule=rule_name,
            Targets=[{
                'Id': 'powerwall-scheduler',
                'Arn': SCHEDULER_LAMBDA_ARN,
                'Input': json.dumps({
                    'backup_reserve_percent': percentage,
                    'schedule_name': schedule_name
                })
            }]
        )

        return cors_response(201, {
            'message': 'Schedule created',
            'rule_name': rule_name,
            'schedule_name': schedule_name
        })

    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        return cors_response(500, {'error': str(e)})


def update_schedule(body: dict) -> dict:
    """Update an existing EventBridge schedule rule."""
    rule_name = body.get('rule_name')
    hour = body.get('hour')
    minute = body.get('minute')
    percentage = body.get('percentage')
    enabled = body.get('enabled')

    if not rule_name:
        return cors_response(400, {'error': 'rule_name is required'})

    if not rule_name.startswith(RULE_PREFIX):
        return cors_response(403, {'error': 'Cannot modify non-PW3Mate rules'})

    events = boto3.client('events')

    try:
        # Toggle enable/disable only
        if enabled is not None and hour is None and minute is None and percentage is None:
            if enabled:
                events.enable_rule(Name=rule_name)
            else:
                events.disable_rule(Name=rule_name)
            return cors_response(200, {'message': f'Schedule {"enabled" if enabled else "disabled"}'})

        # Full update
        if hour is None or minute is None or percentage is None:
            return cors_response(400, {'error': 'hour, minute, and percentage are required for a full update'})

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return cors_response(400, {'error': 'Invalid time values'})

        if not (0 <= percentage <= 100):
            return cors_response(400, {'error': 'Percentage must be between 0 and 100'})

        new_rule_name = build_rule_name(hour, minute, percentage)
        schedule_name = build_schedule_name(hour, minute, percentage)

        # If the rule name changed, delete the old one first
        if new_rule_name != rule_name:
            try:
                events.remove_targets(Rule=rule_name, Ids=['powerwall-scheduler'])
                events.delete_rule(Name=rule_name)
            except events.exceptions.ResourceNotFoundException:
                pass

        state = 'ENABLED' if enabled is not False else 'DISABLED'
        events.put_rule(
            Name=new_rule_name,
            ScheduleExpression=f'cron({minute} {hour} * * ? *)',
            State=state,
            Description=f'PW3Mate: Set Powerwall backup reserve to {percentage}% at {hour:02d}:{minute:02d} UTC'
        )

        events.put_targets(
            Rule=new_rule_name,
            Targets=[{
                'Id': 'powerwall-scheduler',
                'Arn': SCHEDULER_LAMBDA_ARN,
                'Input': json.dumps({
                    'backup_reserve_percent': percentage,
                    'schedule_name': schedule_name
                })
            }]
        )

        return cors_response(200, {
            'message': 'Schedule updated',
            'rule_name': new_rule_name,
            'schedule_name': schedule_name
        })

    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
        return cors_response(500, {'error': str(e)})


def delete_schedule(body: dict) -> dict:
    """Delete an EventBridge schedule rule."""
    rule_name = body.get('rule_name')

    if not rule_name:
        return cors_response(400, {'error': 'rule_name is required'})

    if not rule_name.startswith(RULE_PREFIX):
        return cors_response(403, {'error': 'Cannot delete non-PW3Mate rules'})

    events = boto3.client('events')

    try:
        events.remove_targets(Rule=rule_name, Ids=['powerwall-scheduler'])
        events.delete_rule(Name=rule_name)
        return cors_response(200, {'message': 'Schedule deleted'})
    except events.exceptions.ResourceNotFoundException:
        return cors_response(404, {'error': 'Schedule not found'})
    except Exception as e:
        logger.error(f"Failed to delete schedule: {e}")
        return cors_response(500, {'error': str(e)})


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    """API Gateway proxy Lambda handler."""
    method = event.get('httpMethod', '')
    path = event.get('path', '')
    logger.info(f"Request: {method} {path}")

    # CORS preflight
    if method == 'OPTIONS':
        return cors_response(200, {})

    # Parse body
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return cors_response(400, {'error': 'Invalid JSON body'})

    # Login (no auth required)
    if path == '/api/login' and method == 'POST':
        return handle_login(body)

    # All other routes require a valid token
    headers = event.get('headers', {}) or {}
    auth_header = headers.get('Authorization') or headers.get('authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header else ''

    if not validate_token(token):
        return cors_response(401, {'error': 'Unauthorized'})

    # Route
    if path == '/api/schedules':
        if method == 'GET':
            return list_schedules()
        if method == 'POST':
            return create_schedule(body)
        if method == 'PUT':
            return update_schedule(body)
        if method == 'DELETE':
            return delete_schedule(body)

    return cors_response(404, {'error': 'Not found'})
