# Tesla Powerwall Automation - Troubleshooting Guide

This guide helps you diagnose and fix common issues with your Tesla Powerwall automation system.

## 🔍 **Quick Diagnostics**

### Check System Health
1. **Discord notifications** - Are you receiving them?
2. **Tesla app** - Is backup reserve changing on schedule?
3. **CloudWatch logs** - Any error messages?
4. **Parameter Store** - Are credentials up to date?

### System Status Indicators

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| No Discord notifications | Webhook issue | Check webhook URL |
| Powerwall not changing | Token expired | Refresh tokens manually |
| Lambda timeout errors | Network issues | Check AWS region |
| 401 Unauthorized | Invalid credentials | Update Parameter Store |

---

## 🚨 **Common Issues & Solutions**

### 1. **Token Expired Errors**

**Symptoms:**
- Discord notification: "🚨 Tesla Token Emergency"
- Lambda logs: "401 Client Error: Unauthorized"
- Powerwall backup reserve not changing

**Causes:**
- Refresh token expired (after 3 months)
- Token refresh Lambda not running
- Network issues during token refresh

**Solutions:**

**Quick Fix - Manual Token Refresh:**
```bash
# 1. Go through OAuth flow again to get fresh tokens
# 2. Update Parameter Store with new tokens:

aws ssm put-parameter \
  --name "/tesla/powerwall/access_token" \
  --value "your-new-access-token" \
  --type "SecureString" \
  --overwrite

aws ssm put-parameter \
  --name "/tesla/powerwall/refresh_token" \
  --value "your-new-refresh-token" \
  --type "SecureString" \
  --overwrite
```

**Permanent Fix:**
- Ensure daily token refresh Lambda is running correctly
- Check EventBridge rules are enabled
- Monitor CloudWatch logs for refresh failures

### 2. **Discord Notifications Not Working**

**Symptoms:**
- No Discord messages appearing
- Lambda logs: "Discord webhook not configured"
- System working but no notifications

**Solutions:**

**Check webhook URL:**
```bash
# Verify Parameter Store has correct webhook
aws ssm get-parameter \
  --name "/tesla/powerwall/discord_webhook" \
  --with-decryption
```

**Test webhook manually:**
```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message from Tesla Powerwall system"}'
```

**Common webhook issues:**
- Webhook URL expired (regenerate in Discord)
- Wrong parameter name in Parameter Store
- Discord server permissions changed

### 3. **Lambda Function Errors**

**Symptoms:**
- Functions timing out
- Import errors
- Permission denied errors

**Solutions:**

**Check Lambda logs:**
```bash
# View recent logs
aws logs tail /aws/lambda/tesla-daily-token-refresh --follow

aws logs tail /aws/lambda/tesla-powerwall-scheduler --follow
```

**Common Lambda fixes:**
```bash
# Update function timeout
aws lambda update-function-configuration \
  --function-name tesla-daily-token-refresh \
  --timeout 60

# Update memory allocation
aws lambda update-function-configuration \
  --function-name tesla-powerwall-scheduler \
  --memory-size 256
```

**Missing dependencies:**
- Redeploy with proper `requests` library included
- Check deployment package structure

### 4. **EventBridge Schedule Issues**

**Symptoms:**
- Functions not running on schedule
- Wrong timing
- Missing executions

**Solutions:**

**Check EventBridge rules:**
```bash
# List all rules
aws events list-rules --name-prefix tesla

# Check rule details
aws events describe-rule --name tesla-powerwall-2331-100percent
```

**Common scheduling fixes:**
- Verify cron expressions are correct for your timezone
- Ensure rules are enabled
- Check Lambda permissions for EventBridge

**Timezone debugging:**
```bash
# Current UTC time
date -u

# Convert local time to UTC for cron expressions
# Use online cron calculator: https://crontab.cronhub.io/
```

### 5. **Powerwall Not Responding**

**Symptoms:**
- API calls successful but backup reserve not changing
- Tesla app shows no changes
- Delays in reserve updates

**Solutions:**

**Check Tesla API status:**
```bash
# Test API connectivity
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  "https://fleet-api.prd.eu.vn.cloud.tesla.com/api/1/products"
```

**Common Powerwall issues:**
- Tesla API maintenance windows
- Powerwall firmware updates
- Network connectivity to Tesla servers
- Regional API endpoint issues (use EU for Europe, NA for North America)

### 6. **Parameter Store Access Issues**

**Symptoms:**
- Lambda logs: "Failed to get parameter"
- Permission denied errors
- Missing credentials

**Solutions:**

**Check IAM role permissions:**
```bash
# Verify role exists
aws iam get-role --role-name tesla-powerwall-lambda-role

# Check attached policies
aws iam list-attached-role-policies --role-name tesla-powerwall-lambda-role
aws iam list-role-policies --role-name tesla-powerwall-lambda-role
```

**Verify parameters exist:**
```bash
# List all Tesla parameters
aws ssm get-parameters-by-path \
  --path "/tesla/powerwall" \
  --with-decryption
```

**Fix missing permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:PutParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/tesla/powerwall/*"
    }
  ]
}
```

---

## 🔧 **Advanced Debugging**

### Enable Detailed Logging

**Update Lambda environment variables:**
```bash
aws lambda update-function-configuration \
  --function-name tesla-daily-token-refresh \
  --environment Variables='{LOG_LEVEL=DEBUG}'
```

**CloudWatch Insights queries:**
```sql
-- Find all errors in the last 24 hours
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20

-- Token refresh success rate
fields @timestamp, @message
| filter @message like /Token refresh/
| stats count() by bin(5m)
```

### Test Individual Components

**Test Tesla API directly:**
```python
import requests

# Test token refresh
data = {
    'grant_type': 'refresh_token',
    'client_id': 'your-client-id',
    'refresh_token': 'your-refresh-token'
}

response = requests.post(
    'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token',
    data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)

print(response.status_code, response.json())
```

**Test Discord webhook:**
```python
import requests

webhook_url = "your-discord-webhook"
data = {
    'embeds': [{
        'title': 'Test Notification',
        'description': 'Testing Discord integration',
        'color': 0x00ff00
    }]
}

response = requests.post(webhook_url, json=data)
print(response.status_code)
```

### Performance Optimization

**Lambda cold start issues:**
- Increase memory allocation (faster CPU)
- Use provisioned concurrency for critical functions
- Minimize deployment package size

**API rate limiting:**
- Add exponential backoff retry logic
- Spread out API calls if running multiple systems
- Monitor Tesla API rate limit headers

---

## 📊 **Monitoring & Alerts**

### Set Up CloudWatch Alarms

**Lambda error alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "Tesla-Lambda-Errors" \
  --alarm-description "Alert on Lambda function errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=tesla-powerwall-scheduler
```

**Token refresh failure alarm:**
```bash
aws logs put-metric-filter \
  --log-group-name "/aws/lambda/tesla-daily-token-refresh" \
  --filter-name "TokenRefreshFailures" \
  --filter-pattern "ERROR" \
  --metric-transformations \
    metricName=TokenRefreshErrors,metricNamespace=Tesla/Powerwall,metricValue=1
```

### Health Check Dashboard

Create a simple dashboard to monitor:
- Lambda execution count and duration
- Error rates and success rates  
- Parameter Store access patterns
- Discord notification delivery

---

## 🆘 **Emergency Procedures**

### Complete System Recovery

If everything is broken:

1. **Disable all EventBridge rules** (stop automated execution)
2. **Generate fresh Tesla tokens manually**
3. **Update Parameter Store with new tokens**
4. **Test each Lambda function individually**
5. **Re-enable EventBridge rules one by one**

### Backup Your Configuration

```bash
# Export all parameters
aws ssm get-parameters-by-path \
  --path "/tesla/powerwall" \
  --with-decryption > tesla-backup.json

# Export EventBridge rules
aws events list-rules --name-prefix tesla > eventbridge-backup.json

# Export