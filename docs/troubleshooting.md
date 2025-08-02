# PW3Mate - Complete Troubleshooting Guide

This guide helps you diagnose and fix common issues with your Tesla Powerwall automation system.

## 🔍 **Quick System Health Check**

Before diving into specific issues, check these key indicators:

### **✅ System Health Indicators**
- [ ] **Discord notifications**: Receiving 6 per day (2 token + 4 schedule)
- [ ] **Tesla app**: Backup reserve changes match schedule
- [ ] **AWS CloudWatch**: No error logs in past 24 hours
- [ ] **Parameter Store**: All 5 parameters present and updated

### **🚨 Warning Signs**
- ❌ No Discord notifications for 12+ hours
- ❌ Backup reserve not changing on schedule
- ❌ Error notifications in Discord
- ❌ Lambda function timeouts or failures

---

## 📋 **Diagnostic Checklist**

Run through this checklist to identify your issue category:

| Check | Status | Issue Category |
|-------|--------|----------------|
| Tesla app shows scheduled changes | ✅ / ❌ | [Powerwall Control Issues](#powerwall-control-issues) |
| Discord notifications arriving | ✅ / ❌ | [Notification Issues](#notification-issues) |
| Lambda functions executing | ✅ / ❌ | [AWS Infrastructure Issues](#aws-infrastructure-issues) |
| Tesla tokens valid | ✅ / ❌ | [Authentication Issues](#authentication-issues) |
| EventBridge rules enabled | ✅ / ❌ | [Scheduling Issues](#scheduling-issues) |

---

## 🔐 **Authentication Issues**

### **Issue: "Token Expired" Errors**

**Symptoms:**
- Discord notification: "🚨 Tesla Token Emergency"
- Lambda logs: "401 Client Error: Unauthorized"
- Powerwall backup reserve not changing

**Root Causes:**
- Refresh token expired (after 3 months of no use)
- Daily token refresh Lambda not running
- Tesla API maintenance or changes

**Solutions:**

**Quick Fix - Manual Token Refresh:**
1. **Go through OAuth flow again**:
   - Follow [Token Generation Guide](05-token-generation.md)
   - Get fresh access and refresh tokens
2. **Update Parameter Store**:
   ```bash
   # Via AWS CLI
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
   - Or via AWS Console: Systems Manager → Parameter Store → Edit parameters

**Permanent Fix:**
1. **Check daily token refresh is working**:
   - Go to EventBridge → Rules
   - Verify `PW3Mate-Token-Refresh-*` rules are enabled
   - Check CloudWatch logs for refresh attempts
2. **Test token refresh manually**:
   - Go to Lambda → `PW3Mate-Token-Refresh`
   - Click Test → Create test event: `{}`
   - Should return 200 and update Parameter Store

**Prevention:**
- Monitor Discord for daily refresh notifications
- Set up CloudWatch alarm for token refresh failures
- Keep backup of working refresh token (encrypted)

### **Issue: "Invalid Client Credentials"**

**Symptoms:**
- Lambda logs: "Invalid client_id or client_secret"
- Token refresh fails immediately
- 400 or 401 errors from Tesla API

**Root Causes:**
- Typo in Tesla Client ID or Client Secret
- Tesla application not approved
- Client credentials revoked by Tesla

**Solutions:**
1. **Verify credentials in Parameter Store**:
   - Check `/tesla/powerwall/client_id` format (UUID)
   - Check `/tesla/powerwall/client_secret` starts with `ta-secret.`
   - No extra spaces or characters
2. **Verify Tesla application status**:
   - Go to [Tesla Developer Portal](https://developer.tesla.com/)
   - Check application is "Approved" not "Pending"
3. **Re-enter credentials if needed**:
   - Copy fresh from Tesla Developer Portal
   - Update Parameter Store values

### **Issue: "Refresh Token Invalid"**

**Symptoms:**
- Token refresh works initially then fails
- "Refresh token is expired or invalid" message
- Manual token generation required repeatedly

**Root Causes:**
- Tesla changed token validation
- Long period without refresh (>90 days)
- Tesla account security changes

**Solutions:**
1. **Generate fresh tokens**:
   - Complete OAuth flow from scratch
   - Ensure you're using latest Tesla API endpoints
2. **Check token refresh frequency**:
   - Should run daily at 9 PM and 10 PM UTC
   - Both refreshes should update tokens
3. **Verify Tesla account status**:
   - Log into Tesla mobile app
   - Ensure account is active and not locked

---

## ⚡ **Powerwall Control Issues**

### **Issue: Lambda Succeeds but Powerwall Doesn't Change**

**Symptoms:**
- Lambda returns 200 success
- Discord shows successful notification
- Tesla app backup reserve unchanged

**Root Causes:**
- Powerwall offline or in maintenance mode
- Tesla API accepting but not processing commands
- Wrong site ID being used

**Debugging Steps:**
1. **Check Powerwall status in Tesla app**:
   - Is Powerwall online and operational?
   - Any maintenance notifications?
   - Can you manually change backup reserve?

2. **Verify site ID**:
   ```bash
   # Check Lambda logs for site ID
   aws logs filter-log-events \
     --log-group-name "/aws/lambda/PW3Mate-Powerwall-Scheduler" \
     --filter-pattern "Found Powerwall site ID"
   ```

3. **Test Tesla API directly**:
   - Use Lambda test with different percentage
   - Check if any percentage changes work
   - Try changing via Tesla app for comparison

**Solutions:**
1. **Wait and retry**:
   - Tesla API sometimes has delays (5-15 minutes)
   - Check Tesla app after 15 minutes
2. **Power cycle Powerwall** (if safe to do):
   - Turn off Powerwall via Tesla app
   - Wait 5 minutes, turn back on
   - Retry automation
3. **Contact Tesla support** if Powerwall consistently unresponsive

### **Issue: "No Powerwall Found"**

**Symptoms:**
- Lambda logs: "No Powerwall found"
- 404 status code returned
- System can't locate your Powerwall

**Root Causes:**
- Tesla account doesn't have Powerwall access
- Wrong Tesla account used for tokens
- Powerwall not properly registered with Tesla

**Solutions:**
1. **Verify Tesla account**:
   - Ensure OAuth tokens from correct Tesla account
   - Check Tesla mobile app shows your Powerwall
2. **Check API permissions**:
   - Tesla Fleet API application has `energy_device_data` scope
   - Application approved for energy devices
3. **Re-register if needed**:
   - Contact Tesla to ensure Powerwall linked to account
   - May need to re-pair Powerwall with Tesla account

### **Issue: Backup Reserve Changes to Wrong Percentage**

**Symptoms:**
- System executes but sets wrong percentage
- Expected 100%, got 50% (or vice versa)
- Inconsistent behavior

**Root Causes:**
- EventBridge event payload incorrect
- Multiple schedules conflicting
- Tesla API rate limiting causing partial updates

**Solutions:**
1. **Check EventBridge rules**:
   - Go to EventBridge → Rules
   - Click each rule → View targets
   - Verify JSON payload has correct `backup_reserve_percent`
2. **Check for schedule conflicts**:
   - Ensure schedules don't run too close together
   - 5+ minute gaps between changes recommended
3. **Review execution order**:
   - Check CloudWatch logs timestamps
   - Ensure schedules executing in expected order

---

## 📱 **Notification Issues**

### **Issue: No Discord Notifications**

**Symptoms:**
- Lambda functions succeed but no Discord messages
- System working but silent
- No error messages about notifications

**Root Causes:**
- Discord webhook URL incorrect or expired
- Discord server permissions changed
- Webhook URL not in Parameter Store

**Solutions:**
1. **Test webhook manually**:
   ```bash
   curl -X POST "YOUR_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"content": "Test message from PW3Mate"}'
   ```
2. **Check Parameter Store**:
   - Verify `/tesla/powerwall/discord_webhook` exists
   - URL should start with `https://discord.com/api/webhooks/`
3. **Regenerate webhook**:
   - Discord → Server Settings → Integrations → Webhooks
   - Delete old webhook, create new one
   - Update Parameter Store with new URL

### **Issue: Discord Notifications Malformed**

**Symptoms:**
- Notifications arrive but look wrong
- Missing formatting or data
- Error messages in Discord

**Root Causes:**
- Discord webhook payload format issues
- Missing live data from Tesla API
- Character encoding problems

**Solutions:**
1. **Check notification format**:
   - Look at Lambda logs for Discord API errors
   - Verify embed structure is correct
2. **Test without live data**:
   - Temporarily disable live data inclusion
   - See if basic notifications work
3. **Character encoding**:
   - Check for special characters in schedule names
   - Use only ASCII characters in testing

### **Issue: Too Many Notifications**

**Symptoms:**
- More than 6 notifications per day
- Duplicate notifications
- Notification spam

**Root Causes:**
- Multiple EventBridge rules triggering same function
- Error loops causing retries
- Timezone confusion causing double scheduling

**Solutions:**
1. **Audit EventBridge rules**:
   - List all rules with `PW3Mate` in name
   - Disable duplicates or incorrect rules
2. **Check for error loops**:
   - Review CloudWatch logs for repeated errors
   - Fix underlying issues to stop retries
3. **Verify schedule times**:
   - Ensure cron expressions are correct for your timezone
   - No overlapping schedules

---

## ☁️ **AWS Infrastructure Issues**

### **Issue: Lambda Function Timeouts**

**Symptoms:**
- Lambda logs: "Task timed out after 60.00 seconds"
- Partial execution or incomplete operations
- Intermittent failures

**Root Causes:**
- Network latency to Tesla API
- Parameter Store access delays
- Insufficient memory allocation

**Solutions:**
1. **Increase timeout**:
   - Go to Lambda → Configuration → General
   - Increase timeout to 2-3 minutes
2. **Increase memory**:
   - More memory = faster CPU
   - Try 512MB instead of 256MB
3. **Check network**:
   - Tesla API might be slow
   - Add retry logic with exponential backoff

### **Issue: Parameter Store Access Denied**

**Symptoms:**
- Lambda logs: "Failed to get parameter"
- Permission denied errors
- Unable to read Tesla credentials

**Root Causes:**
- IAM role missing permissions
- Parameter Store permissions too restrictive
- Parameter names incorrect

**Solutions:**
1. **Check IAM role permissions**:
   ```bash
   # Verify role exists and has correct policy
   aws iam get-role --role-name PW3Mate-Lambda-Role
   aws iam list-role-policies --role-name PW3Mate-Lambda-Role
   ```
2. **Required permissions**:
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
3. **Verify parameter names**:
   - Check exact paths: `/tesla/powerwall/client_id`
   - Case sensitive and must match exactly

### **Issue: EventBridge Rules Not Triggering**

**Symptoms:**
- No Lambda executions on schedule
- Rules exist but don't run
- Manual Lambda tests work fine

**Root Causes:**
- Rules disabled
- Cron expressions incorrect
- Lambda permissions missing for EventBridge

**Solutions:**
1. **Check rule status**:
   - EventBridge → Rules → Verify "Enabled"
   - Check cron expressions with online validator
2. **Verify targets**:
   - Each rule should target correct Lambda function
   - Input payloads should be valid JSON
3. **Lambda permissions**:
   ```bash
   # Add EventBridge permission to Lambda
   aws lambda add-permission \
     --function-name PW3Mate-Powerwall-Scheduler \
     --statement-id "EventBridge-PW3Mate" \
     --action lambda:InvokeFunction \
     --principal events.amazonaws.com
   ```

---

## ⏰ **Scheduling Issues**

### **Issue: Wrong Timezone Execution**

**Symptoms:**
- Schedules running at unexpected times
- Local time vs UTC confusion
- Schedules off by several hours

**Root Causes:**
- Cron expressions in wrong timezone
- Daylight saving time confusion
- EventBridge uses UTC only

**Solutions:**
1. **Convert to UTC properly**:
   - **US Eastern**: Add 4-5 hours to desired local time
   - **US Pacific**: Add 7-8 hours to desired local time
   - **Australian Eastern**: Subtract 10-11 hours
2. **Use cron calculator**:
   - [Crontab Guru](https://crontab.guru/) for validation
   - Always verify UTC times
3. **Account for DST**:
   - UTC doesn't change with DST
   - Your local schedules will shift with DST
   - Consider separate winter/summer schedules

### **Issue: Schedules Not Running on Weekends**

**Symptoms:**
- Monday-Friday works fine
- No executions Saturday/Sunday
- EventBridge rules show enabled

**Root Causes:**
- Cron expressions with day-of-week restrictions
- Different weekend schedule needed
- Rules accidentally disabled

**Solutions:**
1. **Check cron expressions**:
   - `* * * * MON-FRI *` only runs weekdays
   - `* * * * ? *` runs every day
2. **Weekend-specific rules**:
   - Create separate rules for weekends if needed
   - Different backup percentages for weekend usage
3. **Verify all rules enabled**:
   - Check each rule individually
   - Enable any disabled weekend rules

---

## 🔧 **Advanced Diagnostics**

### **CloudWatch Log Analysis**

**Check Lambda execution logs:**
```bash
# Token refresh logs
aws logs filter-log-events \
  --log-group-name "/aws/lambda/PW3Mate-Token-Refresh" \
  --start-time $(date -d '1 day ago' +%s)000

# Powerwall scheduler logs
aws logs filter-log-events \
  --log-group-name "/aws/lambda/PW3Mate-Powerwall-Scheduler" \
  --start-time $(date -d '1 day ago' +%s)000
```

**Look for these patterns:**
- ✅ "Token refresh successful"
- ✅ "Successfully set backup reserve"
- ❌ "Failed to get parameter"
- ❌ "401 Client Error: Unauthorized"
- ❌ "Network error during"

### **Tesla API Direct Testing**

**Test token refresh manually:**
```bash
curl --request POST \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=refresh_token' \
  --data-urlencode 'client_id=YOUR_CLIENT_ID' \
  --data-urlencode 'refresh_token=YOUR_REFRESH_TOKEN' \
  'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token'
```

**Test Powerwall status:**
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  "https://fleet-api.prd.eu.vn.cloud.tesla.com/api/1/products"
```

### **Parameter Store Validation**

**Check all parameters exist:**
```bash
aws ssm get-parameters-by-path \
  --path "/tesla/powerwall" \
  --with-decryption \
  --recursive
```

**Expected parameters:**
- `/tesla/powerwall/client_id` - Tesla Client ID (UUID format)
- `/tesla/powerwall/client_secret` - Tesla Client Secret (starts with ta-secret.)
- `/tesla/powerwall/access_token` - Current access token (JWT format)
- `/tesla/powerwall/refresh_token` - Current refresh token (JWT format)
- `/tesla/powerwall/discord_webhook` - Discord webhook URL

### **EventBridge Schedule Validation**

**List all PW3Mate rules:**
```bash
aws events list-rules \
  --name-prefix "PW3Mate" \
  --query 'Rules[*].{Name:Name,State:State,Schedule:ScheduleExpression}'
```

**Expected rules:**
- `PW3Mate-Token-Refresh-Primary` - `cron(0 21 * * ? *)`
- `PW3Mate-Token-Refresh-Backup` - `cron(0 22 * * ? *)`
- `PW3Mate-Powerwall-Schedule1` - Your schedule 1 time
- `PW3Mate-Powerwall-Schedule2` - Your schedule 2 time
- `PW3Mate-Powerwall-Schedule3` - Your schedule 3 time
- `PW3Mate-Powerwall-Schedule4` - Your schedule 4 time

---

## 🚨 **Emergency Procedures**

### **Complete System Failure Recovery**

If your entire system stops working:

**Step 1: Stop Automation**
```bash
# Disable all EventBridge rules
aws events list-rules --name-prefix "PW3Mate" \
  --query 'Rules[*].Name' --output text | \
  xargs -I {} aws events disable-rule --name {}
```

**Step 2: Manual Powerwall Control**
- Use Tesla mobile app to manually set backup reserve
- This always works regardless of automation status
- Set to safe level (50-80%) while troubleshooting

**Step 3: Diagnose Core Issue**
1. Check AWS account status and billing
2. Verify Lambda functions exist and are not corrupted
3. Test Parameter Store access
4. Validate Tesla credentials manually

**Step 4: Systematic Recovery**
1. **Test token refresh first**:
   ```bash
   aws lambda invoke \
     --function-name PW3Mate-Token-Refresh \
     --payload '{}' response.json
   cat response.json
   ```
2. **If token refresh fails**: Generate new tokens via OAuth
3. **If token refresh succeeds**: Test Powerwall control
4. **Re-enable rules one by one**: Start with least critical

**Step 5: Verify Recovery**
- Manual test of each Lambda function
- Check Discord notifications working
- Enable one EventBridge rule and monitor
- Gradually enable all rules

### **Token Emergency Recovery**

**When all tokens are expired/invalid:**

1. **Immediate action**:
   - Use Tesla app for manual control
   - System will not work until tokens refreshed

2. **Token regeneration**:
   - Follow [Token Generation Guide](05-token-generation.md) completely
   - Use fresh OAuth flow from Tesla Developer Portal
   - Update Parameter Store with new tokens

3. **Prevention setup**:
   - Set up CloudWatch alarm for token refresh failures
   - Monitor Discord for daily refresh notifications
   - Keep backup of working refresh token (encrypted)

### **AWS Account Issues**

**If AWS account suspended or billing issues:**

1. **Resolve billing**: Update payment method in AWS Console
2. **Temporary local control**: Use Tesla app exclusively
3. **Data backup**: Export Parameter Store values before account closure
4. **Migration plan**: Can redeploy to new AWS account if needed

---

## 📊 **Monitoring and Alerting Setup**

### **CloudWatch Alarms for Proactive Monitoring**

**Token Refresh Failure Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "PW3Mate-TokenRefresh-Failures" \
  --alarm-description "Alert when token refresh fails" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=PW3Mate-Token-Refresh
```

**Powerwall Scheduler Failure Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "PW3Mate-PowerwallScheduler-Failures" \
  --alarm-description "Alert when Powerwall scheduling fails" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=PW3Mate-Powerwall-Scheduler
```

**Cost Monitoring Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "PW3Mate-Cost-Alert" \
  --alarm-description "Alert when monthly costs exceed $1" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 1.00 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD
```

### **Health Check Dashboard**

Create CloudWatch dashboard to monitor:
- Lambda invocation count (should be 6/day)
- Lambda error rate (should be 0%)
- Lambda duration (should be <10 seconds)
- Parameter Store access patterns
- EventBridge rule execution count

### **Weekly Health Report**

Set up weekly automated health check:
```bash
#!/bin/bash
# Weekly PW3Mate health check script

echo "PW3Mate Weekly Health Report"
echo "============================="

# Check Lambda invocations last 7 days
echo "Lambda Invocations (Last 7 Days):"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=PW3Mate-Token-Refresh \
  --start-time $(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum

# Check for errors
echo "Lambda Errors (Last 7 Days):"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=PW3Mate-Powerwall-Scheduler \
  --start-time $(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum
```

---

## 🔍 **Performance Optimization**

### **Lambda Performance Tuning**

**If Lambda functions are slow:**

1. **Increase memory allocation**:
   - More memory = proportionally more CPU
   - Try 512MB or 1024MB for faster execution

2. **Optimize network calls**:
   - Reduce API call frequency
   - Implement connection pooling
   - Add appropriate timeouts

3. **Parameter Store optimization**:
   - Batch parameter retrieval
   - Cache parameters within execution
   - Use GetParametersByPath for efficiency

### **Cost Optimization**

**If costs are higher than expected:**

1. **Check Lambda duration**:
   - Should be <10 seconds per execution
   - Optimize code to reduce execution time
   - Consider provisioned concurrency if cold starts are issue

2. **Review CloudWatch usage**:
   - Reduce log retention period
   - Filter unnecessary log entries
   - Use log insights efficiently

3. **Parameter Store optimization**:
   - Minimize parameter size
   - Use standard parameters where encryption not needed
   - Clean up unused parameters

### **Reliability Improvements**

**For maximum reliability:**

1. **Implement exponential backoff**:
   - Retry failed Tesla API calls
   - Wait longer between retries
   - Maximum retry attempts

2. **Add circuit breaker pattern**:
   - Stop retrying if Tesla API consistently fails
   - Implement health check before API calls
   - Graceful degradation

3. **Multi-region deployment** (advanced):
   - Deploy to multiple AWS regions
   - Cross-region failover capability
   - Region-specific Tesla API endpoints

---

## 📚 **Common Error Messages**

### **Tesla API Errors**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `401 Unauthorized` | Token expired or invalid | Refresh tokens or regenerate via OAuth |
| `403 Forbidden` | Insufficient permissions | Check Tesla app permissions and scopes |
| `404 Not Found` | Powerwall not found | Verify Tesla account has Powerwall access |
| `429 Too Many Requests` | Rate limiting | Implement exponential backoff, reduce frequency |
| `500 Internal Server Error` | Tesla API issues | Wait and retry, check Tesla service status |
| `503 Service Unavailable` | Tesla maintenance | Wait for maintenance completion |

### **AWS Service Errors**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `ParameterNotFound` | Missing Parameter Store entry | Create missing parameter |
| `AccessDenied` | IAM permissions issue | Add required permissions to IAM role |
| `ThrottlingException` | API rate limiting | Implement retry with backoff |
| `ResourceNotFoundException` | Lambda function missing | Redeploy Lambda function |
| `InvalidParameterValue` | Invalid parameter format | Check parameter value format |

### **Discord API Errors**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `400 Bad Request` | Invalid webhook payload | Check JSON format and embed structure |
| `401 Unauthorized` | Invalid webhook URL | Regenerate webhook in Discord |
| `404 Not Found` | Webhook deleted or expired | Create new webhook |
| `429 Too Many Requests` | Discord rate limiting | Reduce notification frequency |

---

## 🛠️ **Maintenance Tasks**

### **Monthly Maintenance**

1. **Review system performance**:
   - Check CloudWatch metrics
   - Verify 99%+ success rate
   - Review execution duration trends

2. **Cost analysis**:
   - Should remain ~$0.01/month
   - Investigate any cost spikes
   - Optimize if needed

3. **Security review**:
   - Rotate Discord webhook if needed
   - Review IAM permissions
   - Check for AWS security recommendations

### **Quarterly Maintenance**

1. **Tesla credential rotation**:
   - Generate fresh OAuth tokens
   - Update Parameter Store
   - Test system functionality

2. **Schedule optimization**:
   - Review electricity usage patterns
   - Adjust schedules for seasonal changes
   - Optimize backup percentages

3. **Documentation updates**:
   - Update any changed procedures
   - Note any new issues discovered
   - Share improvements with community

### **Annual Maintenance**

1. **Full system review**:
   - Evaluate cost savings achieved
   - Consider new features or optimizations
   - Plan any major upgrades

2. **Disaster recovery test**:
   - Test complete system recovery
   - Verify backup procedures
   - Update emergency contacts

3. **Security audit**:
   - Review all access permissions
   - Update any security policies
   - Consider additional monitoring

---

## 📞 **Getting Additional Help**

### **When to Seek Help**

Seek help when:
- Multiple troubleshooting attempts fail
- System has been down >24 hours
- Cost unexpectedly exceeds $1/month
- Security concerns or suspicious activity
- Want to implement advanced features

### **How to Get Help**

**1. GitHub Community:**
- [GitHub Issues](../../issues) - Report bugs or specific problems
- [GitHub Discussions](../../discussions) - Ask questions and get advice
- Search existing issues before creating new ones

**2. Information to Include:**
When seeking help, include:
- System status (what's working/not working)
- Error messages (from CloudWatch logs)
- Recent changes made to system
- AWS region and approximate setup date
- Screenshots of Discord notifications or AWS console

**3. What NOT to Include:**
Never share:
- Tesla Client ID or Client Secret
- Access tokens or refresh tokens
- Discord webhook URLs
- AWS account numbers or credentials
- Personal identifying information

### **Professional Support Options**

**AWS Support:**
- AWS Technical Support for infrastructure issues
- AWS Architecture reviews for optimization
- AWS Security consultations

**Tesla Support:**
- Tesla Fleet API technical support
- Tesla Developer Portal assistance
- Powerwall hardware issues

**Community Resources:**
- Tesla owners forums
- Reddit r/TeslaPowerwall
- Home automation communities
- AWS user groups

---

## 📈 **Success Metrics**

### **System Health KPIs**

Track these metrics monthly:

| Metric | Target | How to Check |
|--------|--------|--------------|
| Uptime | >99.5% | CloudWatch Lambda success rate |
| Notification delivery | >95% | Discord message count |
| Cost | <$0.05/month | AWS billing dashboard |
| Token refresh success | 100% | CloudWatch logs |
| Schedule accuracy | ±2 minutes | Tesla app vs expected times |

### **Energy Optimization KPIs**

Track these for ROI measurement:

| Metric | Measurement | Tracking Method |
|--------|-------------|-----------------|
| Electricity cost savings | Monthly $ reduction | Utility bill comparison |
| Peak demand reduction | kW reduction | Tesla app energy graphs |
| Solar utilization | % increase | Tesla app solar stats |
| Grid independence | Hours per day | Tesla app power flow |

---

## 🎯 **Prevention Best Practices**

### **Proactive Monitoring**

1. **Set up CloudWatch dashboards**
2. **Configure billing alerts**
3. **Monitor Discord notifications daily**
4. **Weekly Tesla app verification**
5. **Monthly cost review**

### **Security Hygiene**

1. **Rotate credentials quarterly**
2. **Monitor AWS CloudTrail logs**
3. **Keep Tesla app updated**
4. **Review IAM permissions regularly**
5. **Use strong Discord server security**

### **System Reliability**

1. **Test disaster recovery quarterly**
2. **Keep backup of working configuration**
3. **Document any customizations**
4. **Monitor Tesla service status**
5. **Stay updated with AWS service changes**

---

## 🏆 **Advanced Troubleshooting**

### **Deep Debugging Techniques**

**Enable debug logging:**
```python
# Add to Lambda function for detailed debugging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
```

**Trace API calls:**
```python
# Add request/response logging
import requests
import logging

# Enable requests debugging
logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
logging.getLogger("requests.packages.urllib3").propagate = True
```

**Parameter Store debugging:**
```bash
# Test parameter access with AWS CLI
aws ssm get-parameter \
  --name "/tesla/powerwall/client_id" \
  --with-decryption \
  --region your-region
```

### **Network Diagnostics**

**Test Tesla API connectivity:**
```bash
# Test DNS resolution
nslookup fleet-api.prd.eu.vn.cloud.tesla.com

# Test HTTPS connectivity
curl -v https://fleet-api.prd.eu.vn.cloud.tesla.com

# Test with specific user agent
curl -H "User-Agent: PW3Mate/1.0" \
  https://fleet-api.prd.eu.vn.cloud.tesla.com/api/1/status
```

**Check Discord webhook connectivity:**
```bash
# Test webhook URL
curl -v -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "Connection test"}'
```

### **Performance Profiling**

**Lambda execution profiling:**
```python
import time
import functools

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

# Apply to functions for timing analysis
@timing_decorator
def refresh_tesla_tokens():
    # Function implementation
    pass
```

---

**🎉 Congratulations on troubleshooting your PW3Mate system!**

Most issues can be resolved using this guide. Remember:
- **Manual Tesla app control always works** as a backup
- **System recovery is always possible** with fresh token generation
- **Community support is available** through GitHub discussions
- **Your data and Powerwall are always safe** - automation only changes backup reserve

**Still need help?** [Open a GitHub discussion](../../discussions) with details about your specific issue, and the community will help you get back up and running!

**System working again?** Consider contributing back by documenting any new issues you discovered and their solutions.