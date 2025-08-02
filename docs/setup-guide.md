# Tesla Powerwall Automation - Complete Setup Guide

This guide will walk you through setting up fully automated Tesla Powerwall backup reserve scheduling from scratch.

## 🎯 **What You'll Build**

By the end of this guide, you'll have:
- ✅ Automated Powerwall backup reserve scheduling (4 times daily)
- ✅ Dual token refresh system (9 PM + 10 PM for reliability)
- ✅ Beautiful Discord notifications for all operations
- ✅ Zero-maintenance system that runs forever

## ⏱️ **Time Required**
- **First-time setup**: 60-90 minutes
- **If you have AWS experience**: 30-45 minutes

## 📋 **Prerequisites**

### Hardware/Accounts Required:
- [ ] Tesla Powerwall 3 
- [ ] AWS Account with credit card on file
- [ ] Discord account and server
- [ ] Domain name you control (for Tesla Fleet API)

### Skills Needed:
- Basic familiarity with AWS Console
- Ability to copy/paste and follow instructions
- No programming experience required

## 📑 **Overview of Steps**

1. **Tesla Fleet API Setup** (20 minutes)
2. **AWS Infrastructure Setup** (25 minutes)  
3. **Discord Configuration** (5 minutes)
4. **Initial Token Generation** (10 minutes)
5. **System Testing** (10 minutes)
6. **Schedule Deployment** (10 minutes)

---

## 🚗 **Step 1: Tesla Fleet API Setup**

### 1.1 Register for Tesla Developer Account

1. **Go to [Tesla Developer Portal](https://developer.tesla.com/)**
2. **Sign in** with your Tesla account (same as Tesla app)
3. **Click "Get Started"** and complete the developer registration

### 1.2 Create Your Application

1. **Click "Create New App"**
2. **Fill out application details**:
   - **App Name**: `My Powerwall Scheduler`
   - **Description**: `Automated backup reserve scheduling for my personal Powerwall`
   - **Website URL**: `https://your-domain.com` (use a domain you control)
   - **App Type**: `Third-party`
   - **Scopes**: Select:
     - ✅ `openid`
     - ✅ `offline_access` 
     - ✅ `energy_device_data`
     - ✅ `energy_cmds`

3. **Allowed Origins**: `https://your-domain.com`
4. **Redirect URIs**: `https://your-domain.com/oauth/callback`
5. **Submit application**

### 1.3 Wait for Approval
- Tesla typically approves hobby applications within 1-3 business days
- You'll receive email confirmation when approved
- **Don't proceed until approved** - you'll need the client credentials

### 1.4 Get Your Credentials
Once approved:
1. **Sign in to Tesla Developer Portal**
2. **View your approved application**  
3. **Copy and save securely**:
   - `Client ID` (looks like: `4c873630-ec78-47ae-b6af-3ff6c5c228c7`)
   - `Client Secret` (looks like: `ta-secret.H6XG7KkFl3qefM16`)

### 1.5 Set Up Your Domain

You need a website at your registered domain to host a public key file.

**Option A: Use GitHub Pages (Free)**
1. Create GitHub repository: `your-username.github.io`
2. Create file: `.well-known/appspecific/com.tesla.3p.public-key.pem`
3. Generate EC public key (instructions in Tesla docs)
4. Upload the public key file

**Option B: Use AWS S3 + CloudFront**
1. Create S3 bucket with your domain name
2. Enable static website hosting
3. Create CloudFront distribution
4. Upload public key to correct path

**Option C: Use Existing Website**
Upload the public key file to: `https://your-domain.com/.well-known/appspecific/com.tesla.3p.public-key.pem`

---

## ☁️ **Step 2: AWS Infrastructure Setup**

### 2.1 Create IAM Role

1. **Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)**
2. **Click "Roles" → "Create role"**
3. **Configure role**:
   - **Trusted entity**: `AWS service`
   - **Use case**: `Lambda`
   - **Permissions**: `AWSLambdaBasicExecutionRole`
   - **Role name**: `tesla-powerwall-lambda-role`

4. **Add inline policy** for Parameter Store:
   - Click the role → "Add permissions" → "Create inline policy"
   - **JSON tab**, paste:
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
   - **Policy name**: `TeslaPowerwallParameterStoreAccess`

### 2.2 Create Parameter Store Entries

1. **Go to [AWS Systems Manager](https://console.aws.amazon.com/systems-manager/)**
2. **Click "Parameter Store"**
3. **Create these parameters** (one by one):

**Tesla Credentials** (you'll update these later):
```
Name: /tesla/powerwall/client_id
Type: SecureString  
Value: your-client-id-from-tesla

Name: /tesla/powerwall/client_secret
Type: SecureString
Value: your-client-secret-from-tesla

Name: /tesla/powerwall/access_token
Type: SecureString
Value: placeholder-will-update-later

Name: /tesla/powerwall/refresh_token  
Type: SecureString
Value: placeholder-will-update-later
```

**Discord Webhook** (you'll get this in Step 3):
```
Name: /tesla/powerwall/discord_webhook
Type: SecureString
Value: your-discord-webhook-url
```

### 2.3 Create Lambda Functions

**Create Token Refresh Lambda:**
1. **Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)**
2. **Click "Create function"**
3. **Configure**:
   - **Function name**: `tesla-daily-token-refresh`
   - **Runtime**: `Python 3.11`
   - **Execution role**: `tesla-powerwall-lambda-role`
4. **Upload code**: Copy code from `src/lambda/token_refresh/lambda_function.py`  
5. **Configuration**:
   - **Timeout**: 1 minute
   - **Memory**: 256 MB

**Create Powerwall Scheduler Lambda:**
1. **Click "Create function"** 
2. **Configure**:
   - **Function name**: `tesla-powerwall-scheduler`
   - **Runtime**: `Python 3.11`  
   - **Execution role**: `tesla-powerwall-lambda-role`
3. **Upload code**: Copy code from `src/lambda/powerwall_scheduler/lambda_function.py`
4. **Configuration**:
   - **Timeout**: 1 minute
   - **Memory**: 256 MB

---

## 💬 **Step 3: Discord Configuration**

### 3.1 Create Discord Server (if needed)
1. **Open Discord** → Click "+" → "Create a server"  
2. **Name**: `Tesla Powerwall`
3. **Create**

### 3.2 Create Webhook
1. **Right-click server name** → "Server Settings"
2. **Click "Integrations"** → "Webhooks"  
3. **Click "Create Webhook"**
4. **Configure**:
   - **Name**: `Tesla Powerwall Bot`
   - **Channel**: `#general` (or create dedicated channel)
5. **Copy webhook URL** (looks like: `https://discord.com/api/webhooks/123.../abc...`)

### 3.3 Update Parameter Store
1. **Go back to Parameter Store**
2. **Edit `/tesla/powerwall/discord_webhook`**
3. **Paste your webhook URL**

---

## 🔑 **Step 4: Initial Token Generation**

Now we need to complete the OAuth flow to get your first set of tokens.

### 4.1 Register Your App with Tesla Fleet API

First, generate a partner authentication token:
```bash
curl --request POST \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode 'client_id=YOUR_CLIENT_ID' \
  --data-urlencode 'client_secret=YOUR_CLIENT_SECRET' \
  --data-urlencode 'scope=openid energy_device_data energy_cmds offline_access' \
  --data-urlencode 'audience=https://fleet-api.prd.eu.vn.cloud.tesla.com' \
  'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token'
```

Then register your app:
```bash
curl -H "Authorization: Bearer YOUR_PARTNER_TOKEN" \
     -H 'Content-Type: application/json' \
     --data '{"domain": "your-domain.com"}' \
     -X POST \
     -i https://fleet-api.prd.eu.vn.cloud.tesla.com/api/1/partner_accounts
```

### 4.2 User Authorization Flow

1. **Build authorization URL** (replace YOUR_CLIENT_ID and YOUR_DOMAIN):
   ```
   https://auth.tesla.com/oauth2/v3/authorize?client_id=YOUR_CLIENT_ID&locale=en-US&prompt=login&redirect_uri=https://YOUR_DOMAIN/oauth/callback&response_type=code&scope=openid%20energy_device_data%20energy_cmds%20offline_access&state=powerwall2025
   ```

2. **Visit the URL** in your browser
3. **Log in** with your Tesla credentials  
4. **Authorize** the application
5. **Copy the authorization code** from the callback URL

### 4.3 Exchange Code for Tokens

```bash
curl --request POST \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=authorization_code' \
  --data-urlencode 'client_id=YOUR_CLIENT_ID' \
  --data-urlencode 'client_secret=YOUR_CLIENT_SECRET' \
  --data-urlencode 'code=YOUR_AUTHORIZATION_CODE' \
  --data-urlencode 'audience=https://fleet-api.prd.eu.vn.cloud.tesla.com' \
  --data-urlencode 'redirect_uri=https://YOUR_DOMAIN/oauth/callback' \
  'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token'
```

### 4.4 Update Parameter Store

From the token response, update these parameters:
- `/tesla/powerwall/access_token` → `access_token` from response
- `/tesla/powerwall/refresh_token` → `refresh_token` from response

---

## 🧪 **Step 5: System Testing**

### 5.1 Test Token Refresh Lambda

1. **Go to your `tesla-daily-token-refresh` Lambda**
2. **Click "Test"** → **Create new test event**:
   ```json
   {}
   ```
3. **Run test** - should see success message and Discord notification

### 5.2 Test Powerwall Scheduler Lambda  

1. **Go to your `tesla-powerwall-scheduler` Lambda**
2. **Click "Test"** → **Create new test event**:
   ```json
   {
     "backup_reserve_percent": 50,
     "schedule_name": "Manual Test - Set to 50%"
   }
   ```
3. **Run test** - should change your Powerwall backup reserve and send Discord notification

### 5.3 Verify Powerwall Changes

1. **Check Tesla app** - backup reserve should be 50%
2. **Check Discord** - should see beautiful formatted notification with live data

---

## ⏰ **Step 6: Schedule Deployment**

### 6.1 Create EventBridge Rules

**Daily Token Refresh (9 PM):**
1. **Go to [EventBridge Console](https://console.aws.amazon.com/events/)**
2. **Click "Rules" → "Create rule"**
3. **Configure**:
   - **Name**: `tesla-token-refresh-9pm`
   - **Rule type**: `Schedule`
   - **Cron expression**: `cron(0 20 * * ? *)`
   - **Target**: `tesla-daily-token-refresh` Lambda

**Daily Token Refresh (10 PM):**
1. **Create another rule**:
   - **Name**: `tesla-token-refresh-10pm` 
   - **Cron expression**: `cron(0 21 * * ? *)`
   - **Target**: `tesla-daily-token-refresh` Lambda

**Powerwall Schedule (11:31 PM → 100%):**
1. **Create rule**:
   - **Name**: `tesla-powerwall-2331-100percent`
   - **Cron expression**: `cron(31 22 * * ? *)`
   - **Target**: `tesla-powerwall-scheduler` Lambda
   - **Input**: Constant JSON:
     ```json
     {
       "backup_reserve_percent": 100,
       "schedule_name": "11:31 PM - Set to 100%" 
     }
     ```

**Powerwall Schedule (12:29 AM → 0%):**
1. **Create rule**:
   - **Name**: `tesla-powerwall-2329-0percent`
   - **Cron expression**: `cron(29 23 * * ? *)`  
   - **Input**: 
     ```json
     {
       "backup_reserve_percent": 0,
       "schedule_name": "12:29 AM - Set to 0%"
     }
     ```

**Powerwall Schedule (1:31 AM → 100%):**
1. **Create rule**:
   - **Name**: `tesla-powerwall-0131-100percent`
   - **Cron expression**: `cron(31 0 * * ? *)`
   - **Input**:
     ```json
     {
       "backup_reserve_percent": 100, 
       "schedule_name": "1:31 AM - Set to 100%"
     }
     ```

**Powerwall Schedule (5:29 AM → 0%):**
1. **Create rule**:
   - **Name**: `tesla-powerwall-0529-0percent`
   - **Cron expression**: `cron(29 4 * * ? *)`
   - **Input**:
     ```json
     {
       "backup_reserve_percent": 0,
       "schedule_name": "5:29 AM - Set to 0%"
     }
     ```

---

## ✅ **Step 7: Final Verification**

### 7.1 Monitor First Day
- **9:00 PM** → Should see Discord notification: "Daily Tesla Token Refresh"
- **10:00 PM** → Should see Discord notification: "Backup refresh completed"  
- **11:31 PM** → Should see Discord notification + Powerwall changes to 100%
- **12:29 AM** → Should see Discord notification + Powerwall changes to 0%

### 7.2 Check CloudWatch Logs
- Monitor `/aws/lambda/tesla-daily-token-refresh` 
- Monitor `/aws/lambda/tesla-powerwall-scheduler`
- Look for any errors or warnings

### 7.3 Verify Tesla App
Check that your Powerwall backup reserve changes according to schedule.

---

## 🎉 **Congratulations!**

Your Tesla Powerwall automation system is now fully operational! You should see:

✅ **Automated token refresh** twice daily  
✅ **Scheduled backup reserve changes** 4 times daily  
✅ **Beautiful Discord notifications** for all operations  
✅ **Zero maintenance required** - system runs forever  

## 🔧 **Next Steps**

- **Customize schedule**: Modify EventBridge cron expressions for different times
- **Adjust percentages**: Change backup reserve values in EventBridge inputs
- **Add more schedules**: Create additional rules for weekend or seasonal schedules
- **Monitor costs**: Check AWS billing (should be ~$0.01/month)

## 🆘 **Need Help?**

- 📖 **Check**: [Troubleshooting Guide](troubleshooting.md)
- 🐛 **Report Issues**: [GitHub Issues](../../issues)
- 💬 **Ask Questions**: [GitHub Discussions](../../discussions)
- 📧 **Email Support**: Create an issue with detailed logs

## 📊 **Expected Monthly Costs**

Your system will cost approximately **$0.01/month** to run:

| AWS Service | Usage | Monthly Cost |
|-------------|-------|-------------|
| Lambda Executions | ~180/month (6 daily) | $0.006 |
| Lambda Duration | ~30 seconds total | $0.000 |
| Parameter Store | 5 parameters | $0.000 |
| EventBridge Rules | 6 rules, 180 events | $0.000 |
| **Total** | | **~$0.01** |

## 🔄 **Maintenance**

This system requires **zero maintenance** once set up. However, you may want to:

- **Monitor Discord notifications** to ensure everything is working
- **Check Tesla app occasionally** to verify backup reserve changes
- **Update schedule** if your electricity rates change
- **Add new schedules** for seasonal optimization

## 🛡️ **Security Best Practices**

✅ **All credentials encrypted** in AWS Parameter Store  
✅ **IAM role with minimal permissions**  
✅ **No hardcoded secrets** in Lambda functions  
✅ **HTTPS-only communication** with Tesla API  
✅ **Secure Discord webhooks** with limited permissions  

## 📈 **Advanced Customization**

### Custom Schedules
Create different schedules for different scenarios:

**Weekend Schedule** (Friday night different timing):
```json
{
  "backup_reserve_percent": 90,
  "schedule_name": "Friday Night - Set to 90%"
}
```

**Seasonal Schedule** (winter vs summer):
- Use separate EventBridge rules with date ranges
- Higher backup reserves during winter months
- Lower reserves during peak solar production season

**Time-of-Use Optimization**:
- Peak hours: Higher backup reserve (avoid expensive grid power)
- Off-peak hours: Lower backup reserve (maximize solar storage)
- Super off-peak: Minimal backup reserve (charge from cheap grid power)

### Multiple Powerwall Systems
If you have multiple properties:
- Deploy separate Lambda functions for each property
- Use different Parameter Store paths: `/tesla/house1/...`, `/tesla/house2/...`
- Separate Discord channels for each property

### Integration with Other Systems
- **Home Assistant**: Call Lambda functions from HA automations
- **IFTTT**: Trigger schedules based on weather or energy prices
- **Smart Home**: Integrate with other energy management systems

## 🔍 **Understanding the Architecture**

### Token Management Flow
```
Day 1: Refresh Token A (90 days remaining)
       ↓ (9 PM refresh)
       Access Token 1 + Refresh Token B (90 days remaining)
       ↓ (Token A now invalid)
       
Day 2: Refresh Token B (89 days remaining)  
       ↓ (9 PM refresh)
       Access Token 2 + Refresh Token C (90 days remaining)
       ↓ (Token B now invalid)
       
...continues forever...
```

### Why Dual Refresh (9 PM + 10 PM)?
- **Redundancy**: If 9 PM fails, 10 PM succeeds
- **Network issues**: Temporary Tesla API problems won't break your system
- **AWS maintenance**: Lambda cold starts or regional issues covered
- **Peace of mind**: 99.99% reliability vs 99.9% with single refresh

### EventBridge Scheduling
All times in UTC (Universal Coordinated Time):
- **9 PM UTC** = 9 PM UK (winter) / 8 PM UK (summer)
- **Adjust for your timezone** by modifying cron expressions
- **Daylight Saving Time**: EventBridge uses UTC, so times stay consistent

## 🌍 **Timezone Configuration**

The setup guide uses UK timezone examples. For other timezones:

### US Eastern Time
- **9 PM ET** = `cron(0 1 * * ? *)` (next day UTC)
- **11:31 PM ET** = `cron(31 3 * * ? *)` (next day UTC)

### US Pacific Time  
- **9 PM PT** = `cron(0 4 * * ? *)` (next day UTC)
- **11:31 PM PT** = `cron(31 6 * * ? *)` (next day UTC)

### Australian Eastern Time
- **9 PM AEST** = `cron(0 10 * * ? *)` (same day UTC)
- **11:31 PM AEST** = `cron(31 12 * * ? *)` (same day UTC)

### Calculator
Use [Cron Expression Calculator](https://crontab.cronhub.io/) to convert your local times to UTC cron expressions.

## 📋 **Pre-Deployment Checklist**

Before going live, verify:

**Tesla Fleet API:**
- [ ] Developer account approved
- [ ] Application created and approved
- [ ] Public key hosted at correct URL
- [ ] Partner account registered
- [ ] Initial tokens generated and working

**AWS Infrastructure:**
- [ ] IAM role created with correct permissions
- [ ] Parameter Store populated with all credentials
- [ ] Both Lambda functions deployed and tested
- [ ] Lambda functions can access Parameter Store
- [ ] EventBridge rules created with correct timing

**Discord Setup:**
- [ ] Webhook created and tested
- [ ] Webhook URL stored in Parameter Store
- [ ] Test notifications working and formatted correctly

**End-to-End Testing:**
- [ ] Manual Lambda tests successful
- [ ] Powerwall backup reserve changes confirmed in Tesla app
- [ ] Discord notifications received and properly formatted
- [ ] No errors in CloudWatch logs

**Schedule Verification:**
- [ ] All EventBridge rules created
- [ ] Cron expressions correct for your timezone
- [ ] Event payloads have correct backup percentages
- [ ] Rules enabled and active

## 🚨 **Important Notes**

### Tesla API Limits
- **Rate limiting**: Tesla may throttle requests if you call too frequently
- **Regional endpoints**: Use EU endpoint if you're in Europe, NA for North America
- **Maintenance windows**: Tesla occasionally has maintenance that may cause temporary failures

### AWS Considerations
- **Region selection**: Deploy in a region close to you for better performance
- **Billing alerts**: Set up AWS billing alerts to monitor costs
- **Lambda cold starts**: First execution of the day may take longer

### Powerwall Safety
- **Monitor initially**: Watch your system for the first week to ensure it's working as expected
- **Emergency override**: You can always manually change backup reserve in Tesla app
- **Grid requirements**: Ensure your automation complies with local utility requirements

## 🔮 **Future Enhancements**

Potential improvements for future versions:

### Smart Scheduling
- **Weather integration**: Higher backup reserve when storms predicted
- **Energy price integration**: Dynamic scheduling based on real-time electricity prices
- **Solar forecast**: Adjust backup reserve based on next-day solar prediction

### Advanced Notifications
- **SMS alerts**: Add AWS SNS for critical failures
- **Email reports**: Weekly/monthly energy optimization reports
- **Grafana dashboards**: Visualize energy flows and backup reserve changes over time

### Machine Learning
- **Usage pattern learning**: Automatically optimize schedule based on your energy usage
- **Predictive maintenance**: Alert before tokens expire or system issues occur
- **Cost optimization**: Recommend schedule changes to minimize electricity costs

---

**🎉 Congratulations on building your automated Tesla Powerwall system!**

Your Powerwall will now optimize itself 24/7, saving you money and maximizing your solar energy usage. The system is designed to run indefinitely without any maintenance required.

**Questions?** Check our [troubleshooting guide](troubleshooting.md) or [open an issue](../../issues) on GitHub.

**Working great?** ⭐ Star this repository to help others find it!