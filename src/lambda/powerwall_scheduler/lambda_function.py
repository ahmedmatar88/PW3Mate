"""
Tesla Powerwall Lambda Scheduler with Push Notifications
Supports multiple notification methods: Pushover, SNS, Email, Discord/Slack
"""

import json
import boto3
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TeslaFleetClient:
    """Simplified Tesla Fleet API client for Lambda"""
    
    def __init__(self, client_id: str, client_secret: str, region: str = "eu"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        
        # API endpoints
        self.auth_base = "https://fleet-auth.prd.vn.cloud.tesla.com"
        self.api_base = f"https://fleet-api.prd.{region}.vn.cloud.tesla.com"
        
        # Token storage
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
        # HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PW3Control-Lambda/1.0'
        })

    def set_tokens(self, access_token: str, refresh_token: str):
        """Set authentication tokens"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}'
        })
        
        logger.info("Tokens set successfully")

    def refresh_access_token(self) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Refresh the access token using refresh token
        
        Returns:
            tuple: (success, new_access_token, new_refresh_token)
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False, None, None

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': self.refresh_token
        }

        try:
            logger.info("Attempting to refresh access token...")
            response = requests.post(
                f"{self.auth_base}/oauth2/v3/token",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            logger.info(f"Token refresh response status: {response.status_code}")
            
            if response.status_code == 401:
                logger.error("Refresh token is invalid or expired - manual token regeneration required")
                return False, None, None
            
            response.raise_for_status()
            
            token_data = response.json()
            new_access_token = token_data['access_token']
            
            # Tesla may or may not provide a new refresh token
            # If they don't provide one, keep using the existing one
            new_refresh_token = token_data.get('refresh_token', self.refresh_token)
            
            self.set_tokens(new_access_token, new_refresh_token)
            
            logger.info("Access token refreshed successfully")
            if new_refresh_token != self.refresh_token:
                logger.info("New refresh token provided by Tesla")
            else:
                logger.info("Reusing existing refresh token")
            
            return True, new_access_token, new_refresh_token
            
        except requests.exceptions.Timeout:
            logger.error("Token refresh timed out")
            return False, None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh network error: {e}")
            return False, None, None
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return False, None, None

    def api_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make authenticated API request"""
        url = f"{self.api_base}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None

    def get_products(self) -> Optional[Dict[str, Any]]:
        """Get list of all products"""
        return self.api_request('GET', '/api/1/products')

    def find_powerwall_site(self) -> Optional[str]:
        """Find the first Powerwall site ID"""
        products = self.get_products()
        if not products or 'response' not in products:
            return None
            
        for product in products['response']:
            if product.get('device_type') == 'energy' and product.get('resource_type') == 'battery':
                return str(product['energy_site_id'])
        
        return None

    def get_site_info(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get site information including backup reserve"""
        return self.api_request('GET', f'/api/1/energy_sites/{site_id}/site_info')

    def get_live_status(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get live status data from energy site"""
        return self.api_request('GET', f'/api/1/energy_sites/{site_id}/live_status')

    def set_backup_reserve(self, site_id: str, percent: int) -> Optional[Dict[str, Any]]:
        """Set backup reserve percentage"""
        logger.info(f"Setting backup reserve to {percent}%...")
        
        # Get current backup reserve
        current_info = self.get_site_info(site_id)
        current_reserve = None
        if current_info:
            current_reserve = current_info.get('response', {}).get('backup_reserve_percent', 'Unknown')
            logger.info(f"Current backup reserve: {current_reserve}%")
        
        # Set new backup reserve
        data = {'backup_reserve_percent': percent}
        result = self.api_request('POST', f'/api/1/energy_sites/{site_id}/backup', json=data)
        
        if result:
            logger.info(f"✅ Backup reserve set to {percent}% successfully")
            return {
                'success': True,
                'old_reserve': current_reserve,
                'new_reserve': percent
            }
        else:
            logger.error(f"❌ Failed to set backup reserve to {percent}%")
            return None


class ParameterStoreManager:
    """Manage Tesla credentials in AWS Parameter Store"""
    
    def __init__(self):
        self.ssm = boto3.client('ssm')
        self.parameter_prefix = '/tesla/powerwall'
    
    def get_parameter(self, name: str, decrypt: bool = True) -> Optional[str]:
        """Get parameter from Parameter Store - returns None if not found"""
        try:
            response = self.ssm.get_parameter(
                Name=f"{self.parameter_prefix}/{name}",
                WithDecryption=decrypt
            )
            return response['Parameter']['Value']
        except self.ssm.exceptions.ParameterNotFound:
            # Parameter doesn't exist - this is OK for optional parameters
            logger.debug(f"Parameter {name} not found (optional)")
            return None
        except Exception as e:
            logger.error(f"Failed to get parameter {name}: {e}")
            return None
    
    def put_parameter(self, name: str, value: str, encrypt: bool = True):
        """Store parameter in Parameter Store"""
        try:
            self.ssm.put_parameter(
                Name=f"{self.parameter_prefix}/{name}",
                Value=value,
                Type='SecureString' if encrypt else 'String',
                Overwrite=True
            )
            logger.info(f"Stored parameter {name}")
        except Exception as e:
            logger.error(f"Failed to store parameter {name}: {e}")
    
    def get_all_credentials(self) -> Dict[str, str]:
        """Get all Tesla credentials"""
        return {
            'client_id': self.get_parameter('client_id'),
            'client_secret': self.get_parameter('client_secret'),
            'access_token': self.get_parameter('access_token'),
            'refresh_token': self.get_parameter('refresh_token')
        }
    
    def get_notification_credentials(self) -> Dict[str, str]:
        """Get notification credentials - only returns configured ones"""
        creds = {}
        
        # Only try to get parameters that might exist
        optional_params = [
            'pushover_token', 'pushover_user', 'sns_topic_arn', 
            'discord_webhook', 'notification_email'
        ]
        
        for param in optional_params:
            value = self.get_parameter(param)
            if value:  # Only include if parameter exists and has value
                creds[param] = value
            
        return creds
    
    def update_tokens(self, access_token: str, refresh_token: str):
        """Update stored tokens"""
        self.put_parameter('access_token', access_token)
        self.put_parameter('refresh_token', refresh_token)


class NotificationManager:
    """Handle various notification methods"""
    
    def __init__(self, credentials: Dict[str, str]):
        self.creds = credentials
        
    def send_pushover_notification(self, title: str, message: str, priority: int = 0):
        """Send push notification via Pushover"""
        if not (self.creds.get('pushover_token') and self.creds.get('pushover_user')):
            logger.info("Pushover credentials not configured, skipping")
            return False
            
        try:
            data = {
                'token': self.creds['pushover_token'],
                'user': self.creds['pushover_user'],
                'title': title,
                'message': message,
                'priority': priority,
                'sound': 'pushover'  # Can customize: pushover, bike, bugle, cashregister, classical, cosmic, falling, gamelan, incoming, intermission, magic, mechanical, pianobar, siren, spacealarm, tugboat, alien, climb, persistent, echo, updown, none
            }
            
            response = requests.post('https://api.pushover.net/1/messages.json', data=data)
            response.raise_for_status()
            
            logger.info("✅ Pushover notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Pushover notification: {e}")
            return False
    
    def send_sns_notification(self, message: str):
        """Send SMS via AWS SNS"""
        if not self.creds.get('sns_topic_arn'):
            logger.info("SNS topic not configured, skipping")
            return False
            
        try:
            sns = boto3.client('sns')
            sns.publish(
                TopicArn=self.creds['sns_topic_arn'],
                Message=message,
                Subject='Tesla Powerwall Update'
            )
            
            logger.info("✅ SNS notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send SNS notification: {e}")
            return False
    
    def send_discord_notification(self, message: str):
        """Send message to Discord via webhook"""
        if not self.creds.get('discord_webhook'):
            logger.info("Discord webhook not configured, skipping")
            return False
            
        try:
            # Parse title and message if they're combined
            if message.startswith("**") and "**\n" in message:
                parts = message.split("**\n", 1)
                title = parts[0].replace("**", "")
                content = parts[1] if len(parts) > 1 else message
            else:
                title = "Tesla Powerwall Bot"
                content = message
            
            # Determine color based on message content
            color = 0x00ff00  # Green for success
            if "❌" in message or "Error" in message:
                color = 0xff0000  # Red for errors
            elif "⚠️" in message or "Warning" in message:
                color = 0xffa500  # Orange for warnings
            
            data = {
                'embeds': [{
                    'title': title,
                    'description': content,
                    'color': color,
                    'timestamp': datetime.utcnow().isoformat(),
                    'footer': {
                        'text': 'Tesla Powerwall Scheduler'
                    }
                }],
                'username': 'Tesla Powerwall Bot',
                'avatar_url': 'https://cdn-icons-png.flaticon.com/512/2814/2814666.png'
            }
            
            response = requests.post(self.creds['discord_webhook'], json=data)
            response.raise_for_status()
            
            logger.info("✅ Discord notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Discord notification: {e}")
            return False
    
    def send_email_notification(self, subject: str, message: str):
        """Send email via AWS SES"""
        if not self.creds.get('notification_email'):
            logger.info("Notification email not configured, skipping")
            return False
            
        try:
            ses = boto3.client('ses')
            ses.send_email(
                Source=self.creds['notification_email'],
                Destination={'ToAddresses': [self.creds['notification_email']]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': message}}
                }
            )
            
            logger.info("✅ Email notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email notification: {e}")
            return False
    
    def send_all_notifications(self, title: str, message: str, include_live_data: bool = True, site_id: str = None, tesla_client: TeslaFleetClient = None):
        """Send notifications via all configured methods"""
        
        # Add live data if requested
        full_message = message
        if include_live_data and site_id and tesla_client:
            try:
                live_status = tesla_client.get_live_status(site_id)
                if live_status:
                    response = live_status.get('response', {})
                    battery_level = response.get('percentage_charged', 'Unknown')
                    battery_power = response.get('battery_power', 0)
                    solar_power = response.get('solar_power', 0)
                    home_power = response.get('load_power', 0)
                    
                    status_text = f"\n\n📊 Current Status:\n"
                    status_text += f"🔋 Battery: {battery_level}%\n"
                    status_text += f"⚡ Battery Power: {battery_power}W {'(charging)' if battery_power < 0 else '(discharging)'}\n"
                    status_text += f"☀️ Solar: {solar_power}W\n"
                    status_text += f"🏠 Home Usage: {home_power}W"
                    
                    full_message += status_text
            except Exception as e:
                logger.warning(f"Could not get live data for notification: {e}")
        
        # Send via all configured methods
        results = []
        results.append(self.send_pushover_notification(title, full_message))
        results.append(self.send_sns_notification(full_message))
        results.append(self.send_discord_notification(f"**{title}**\n{full_message}"))
        results.append(self.send_email_notification(title, full_message))
        
        sent_count = sum(results)
        logger.info(f"📱 Sent {sent_count} notifications successfully")
        
        return sent_count > 0


def lambda_handler(event, context):
    """
    AWS Lambda handler for Tesla Powerwall backup reserve scheduling with notifications
    
    Expected event format:
    {
        "backup_reserve_percent": 100,
        "schedule_name": "11:31 PM - Set to 100%"
    }
    """
    logger.info("Tesla Powerwall Lambda Scheduler started")
    logger.info(f"Event received: {json.dumps(event)}")
    
    try:
        # Extract backup reserve percentage from event
        backup_reserve_percent = event.get('backup_reserve_percent')
        schedule_name = event.get('schedule_name', 'Unknown schedule')
        
        if backup_reserve_percent is None:
            logger.error("No backup_reserve_percent provided in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'backup_reserve_percent required in event'})
            }
        
        logger.info(f"Executing schedule: {schedule_name} -> {backup_reserve_percent}%")
        
        # Initialize Parameter Store manager
        param_store = ParameterStoreManager()
        
        # Get credentials from Parameter Store
        tesla_credentials = param_store.get_all_credentials()
        notification_credentials = param_store.get_notification_credentials()
        
        if not all(tesla_credentials.values()):
            logger.error("Missing Tesla credentials in Parameter Store")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Missing Tesla credentials in Parameter Store'})
            }
        
        # Initialize Tesla client
        tesla_client = TeslaFleetClient(
            tesla_credentials['client_id'], 
            tesla_credentials['client_secret'], 
            region="eu"
        )
        
        # Use stored tokens (refreshed daily at 9 PM and 10 PM)
        tesla_client.set_tokens(tesla_credentials['access_token'], tesla_credentials['refresh_token'])
        
        # Check if tokens are likely expired (access tokens last 8 hours)
        # If daily refresh failed, we might need to refresh here as backup
        last_refresh = param_store.get_parameter('last_token_refresh', decrypt=False)
        
        try:
            if last_refresh:
                last_refresh_time = datetime.fromisoformat(last_refresh.replace('Z', '+00:00'))
                hours_since_refresh = (datetime.utcnow() - last_refresh_time.replace(tzinfo=None)).total_seconds() / 3600
                
                if hours_since_refresh > 8:
                    logger.warning(f"Access token likely expired ({hours_since_refresh:.1f} hours old). Attempting refresh as backup.")
                    success, new_access_token, new_refresh_token = tesla_client.refresh_access_token()
                    
                    if success and new_access_token:
                        param_store.update_tokens(new_access_token, new_refresh_token)
                        logger.info("✅ Backup token refresh successful")
                    else:
                        logger.error("❌ Backup token refresh failed - proceeding with stored tokens")
                else:
                    logger.info(f"Using stored access token (refreshed {hours_since_refresh:.1f} hours ago)")
            else:
                logger.info("No last refresh timestamp found - using stored tokens")
        except Exception as e:
            logger.warning(f"Could not check token age: {e} - proceeding with stored tokens")
        
        # Find Powerwall site
        site_id = tesla_client.find_powerwall_site()
        if not site_id:
            error_msg = "No Powerwall found"
            logger.error(error_msg)
            
            # Send failure notification
            notifier = NotificationManager(notification_credentials)
            notifier.send_all_notifications(
                "❌ Tesla Powerwall Error", 
                f"No Powerwall found for {schedule_name}",
                include_live_data=False
            )
            
            return {
                'statusCode': 404,
                'body': json.dumps({'error': error_msg})
            }
        
        logger.info(f"Found Powerwall site ID: {site_id}")
        
        # Set the backup reserve to the specified percentage
        result = tesla_client.set_backup_reserve(site_id, backup_reserve_percent)
        
        # Initialize notification manager
        notifier = NotificationManager(notification_credentials)
        
        if result and result.get('success'):
            success_message = f"Successfully set backup reserve to {backup_reserve_percent}%"
            logger.info(success_message)
            
            # Send success notification with live data
            notification_title = f"✅ Tesla Powerwall Updated"
            notification_message = f"{schedule_name}\n\nBackup reserve changed: {result.get('old_reserve', '?')}% → {backup_reserve_percent}%"
            
            notifier.send_all_notifications(
                notification_title, 
                notification_message,
                include_live_data=True,
                site_id=site_id,
                tesla_client=tesla_client
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': success_message,
                    'site_id': site_id,
                    'backup_reserve': backup_reserve_percent,
                    'schedule_name': schedule_name,
                    'old_reserve': result.get('old_reserve'),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        else:
            error_message = f"Failed to set backup reserve to {backup_reserve_percent}%"
            logger.error(error_message)
            
            # Send failure notification
            notifier.send_all_notifications(
                "❌ Tesla Powerwall Error", 
                f"Failed to execute {schedule_name}. Could not set backup reserve to {backup_reserve_percent}%.",
                include_live_data=False
            )
            
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'{error_message} ({schedule_name})'})
            }
    
    except Exception as e:
        error_msg = f"Lambda execution failed: {str(e)}"
        logger.error(error_msg)
        
        # Send critical failure notification
        try:
            param_store = ParameterStoreManager()
            notification_credentials = param_store.get_notification_credentials()
            notifier = NotificationManager(notification_credentials)
            notifier.send_all_notifications(
                "🚨 Tesla Powerwall Critical Error", 
                f"Lambda function crashed during {event.get('schedule_name', 'unknown schedule')}.\n\nError: {str(e)}",
                include_live_data=False
            )
        except:
            pass  # Don't let notification failure prevent error response
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }


# For local testing
if __name__ == "__main__":
    # Mock Lambda context for local testing
    class MockContext:
        def __init__(self):
            self.function_name = "tesla-powerwall-scheduler"
            self.memory_limit_in_mb = 512
            self.invoked_function_arn = "arn:aws:lambda:eu-west-1:123456789012:function:tesla-powerwall-scheduler"
            self.aws_request_id = "test-request-id"
    
    # Test the handler with sample event
    test_event = {
        "backup_reserve_percent": 100,
        "schedule_name": "Test - Set to 100%"
    }
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))