"""
Tesla Daily Token Refresh Lambda
Runs daily at 11:00 PM to refresh tokens before scheduled events
"""

import json
import boto3
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        
        # Only get Discord webhook for now
        discord_webhook = self.get_parameter('discord_webhook')
        if discord_webhook:
            creds['discord_webhook'] = discord_webhook
            
        return creds
    
    def update_tokens(self, access_token: str, refresh_token: str):
        """Update stored tokens"""
        self.put_parameter('access_token', access_token)
        self.put_parameter('refresh_token', refresh_token)
        
        # Store the refresh timestamp
        self.put_parameter('last_token_refresh', datetime.utcnow().isoformat(), encrypt=False)


def refresh_tesla_tokens(credentials: Dict[str, str]) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Refresh Tesla tokens
    
    Returns:
        tuple: (success, new_access_token, new_refresh_token, message)
    """
    
    if not all(credentials.values()):
        return False, None, None, 'Missing credentials in Parameter Store'
    
    data = {
        'grant_type': 'refresh_token',
        'client_id': credentials['client_id'],
        'refresh_token': credentials['refresh_token']
    }
    
    try:
        logger.info("Refreshing Tesla tokens...")
        response = requests.post(
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        if response.status_code == 401:
            error_msg = "Refresh token is expired or invalid - manual regeneration required"
            logger.error(error_msg)
            return False, None, None, error_msg
        
        response.raise_for_status()
        token_data = response.json()
        
        new_access_token = token_data['access_token']
        new_refresh_token = token_data.get('refresh_token', credentials['refresh_token'])
        
        success_msg = f"Token refresh successful. New refresh token provided: {'Yes' if new_refresh_token != credentials['refresh_token'] else 'No'}"
        logger.info(success_msg)
        
        return True, new_access_token, new_refresh_token, success_msg
        
    except requests.exceptions.Timeout:
        error_msg = "Token refresh request timed out"
        logger.error(error_msg)
        return False, None, None, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during token refresh: {str(e)}"
        logger.error(error_msg)
        return False, None, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error during token refresh: {str(e)}"
        logger.error(error_msg)
        return False, None, None, error_msg


def send_discord_notification(webhook_url: str, title: str, message: str, color: int = 0x00ff00):
    """Send notification to Discord"""
    if not webhook_url:
        logger.info("No Discord webhook configured")
        return False
        
    try:
        data = {
            'embeds': [{
                'title': title,
                'description': message,
                'color': color,
                'timestamp': datetime.utcnow().isoformat(),
                'footer': {
                    'text': 'Tesla Daily Token Refresh'
                }
            }]
        }
        
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
        
        logger.info("Discord notification sent successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False


def lambda_handler(event, context):
    """
    AWS Lambda handler for daily Tesla token refresh
    Runs at 11:00 PM to refresh tokens before scheduled Powerwall events
    """
    logger.info("Daily Tesla Token Refresh started")
    
    try:
        # Initialize Parameter Store manager
        param_store = ParameterStoreManager()
        
        # Get credentials
        tesla_credentials = param_store.get_all_credentials()
        notification_credentials = param_store.get_notification_credentials()
        
        # Refresh tokens
        success, new_access_token, new_refresh_token, message = refresh_tesla_tokens(tesla_credentials)
        
        discord_webhook = notification_credentials.get('discord_webhook')
        
        if success:
            # Update stored tokens
            param_store.update_tokens(new_access_token, new_refresh_token)
            
            logger.info("✅ Daily token refresh completed successfully")
            
            # Send success notification for EVERY successful run
            current_time = datetime.utcnow()
            success_message = f"✅ **Tesla Token Refresh Successful**\n\n"
            success_message += f"🕘 **Time**: {current_time.strftime('%I:%M %p')} UTC\n"
            success_message += f"🔄 **New tokens generated and stored**\n"
            success_message += f"⏰ **Access token valid until**: {(current_time.replace(microsecond=0) + timedelta(hours=8)).strftime('%I:%M %p')} UTC\n"
            success_message += f"📅 **Refresh token valid for**: 3 months\n\n"
            success_message += f"🔋 **Ready for tonight's Powerwall schedule**:\n"
            success_message += f"• 11:31 PM → 100%\n"
            success_message += f"• 12:29 AM → 0%\n" 
            success_message += f"• 1:31 AM → 100%\n"
            success_message += f"• 5:29 AM → 0%\n\n"
            
            # Add extra info for backup refresh (10 PM run)
            if current_time.hour == 21:  # 10 PM UTC
                success_message += f"🛡️ **Backup refresh completed** - System is extra secure!\n"
            else:
                success_message += f"🔄 **Next refresh**: Tomorrow at this time\n"
            
            success_message += f"📊 **All systems operational** ✅"
            
            send_discord_notification(
                discord_webhook,
                "🔋 Daily Tesla Token Refresh",
                success_message,
                0x00ff00  # Green
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'message': 'Daily token refresh completed',
                    'tokens_updated': True,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
            
        else:
            # Token refresh failed
            logger.error(f"❌ Daily token refresh failed: {message}")
            
            # Determine notification urgency
            if "expired" in message.lower() or "invalid" in message.lower():
                # Critical: Manual intervention needed
                error_message = f"🚨 **URGENT: Tesla Token Emergency**\n\n"
                error_message += f"Daily token refresh failed: {message}\n\n"
                error_message += f"**IMPACT:** Tonight's Powerwall schedule will NOT work!\n"
                error_message += f"• 11:31 PM → 100% ❌\n"
                error_message += f"• 12:29 AM → 0% ❌\n"
                error_message += f"• 1:31 AM → 100% ❌\n"
                error_message += f"• 5:29 AM → 0% ❌\n\n"
                error_message += f"**ACTION REQUIRED:**\n"
                error_message += f"1. Generate new tokens via OAuth flow\n"
                error_message += f"2. Update Parameter Store\n"
                error_message += f"3. System will resume automatically"
                
                send_discord_notification(
                    discord_webhook,
                    "🚨 Tesla Token EMERGENCY",
                    error_message,
                    0xff0000  # Red
                )
            else:
                # Temporary error
                error_message = f"⚠️ **Tesla Token Refresh Warning**\n\n"
                error_message += f"Daily token refresh failed: {message}\n\n"
                error_message += f"This might be a temporary network issue.\n"
                error_message += f"**If this persists, manual token regeneration may be needed.**\n\n"
                error_message += f"Tonight's schedule may still work with existing tokens if they haven't expired."
                
                send_discord_notification(
                    discord_webhook,
                    "⚠️ Tesla Token Warning",
                    error_message,
                    0xffa500  # Orange
                )
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'failed',
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
    except Exception as e:
        error_msg = f"Daily token refresh crashed: {str(e)}"
        logger.error(error_msg)
        
        # Send critical error notification
        try:
            param_store = ParameterStoreManager()
            discord_webhook = param_store.get_parameter('discord_webhook')
            
            crash_message = f"💥 **Tesla Daily Token Refresh Crashed**\n\n"
            crash_message += f"The daily token refresh Lambda crashed:\n\n"
            crash_message += f"```{str(e)}```\n\n"
            crash_message += f"**IMPACT:** Tonight's Powerwall schedule may fail if tokens expire!"
            
            send_discord_notification(
                discord_webhook,
                "💥 Tesla System Crash",
                crash_message,
                0x800080  # Purple
            )
        except:
            pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }


if __name__ == "__main__":
    # For local testing
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2))