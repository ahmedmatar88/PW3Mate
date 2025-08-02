# AWS Infrastructure Setup (UI Guide)

This guide walks you through setting up the AWS infrastructure using the AWS Console web interface. No command line required!

## 🎯 **What You'll Build**

- 2 Lambda functions (token refresh + Powerwall scheduling)
- IAM role with proper permissions
- Parameter Store for secure credential storage
- EventBridge schedules for automation

**Time Required:** 30 minutes

---

## 📋 **Prerequisites**

- AWS Account with billing set up
- Tesla Fleet API credentials from previous step
- Discord webhook URL

---

## 🔐 **Step 1: Create IAM Role**

### 1.1 Navigate to IAM

1. **Sign in to [AWS Console](https://console.aws.amazon.com/)**
2. **Search for "IAM"** in the search bar
3. **Click "IAM"** to open the Identity and Access Management console

### 1.2 Create Role

1. **Click "Roles"** in the left sidebar
2. **Click "Create role"**
3. **Trusted entity type**: `AWS service`
4. **Use case**: `Lambda`
5. **Click "Next"**

### 1.3 Attach Permissions

1. **Search for**: `AWSLambdaBasicExecutionRole`
2. **Check the box** next to `AWSLambdaBasicExecutionRole`
3. **Click "Next"**

### 1.4 Name and Create Role

1. **Role name**: `PW3Mate-Lambda-Role`
2. **Description**: `IAM role for PW3Mate Tesla Powerwall automation`
3. **Click "Create role"**

### 1.5 Add Parameter Store Permissions

1. **Find your new role** in the roles list
2. **Click on "PW3Mate-Lambda-Role"**
3. **Click "Add permissions"** → **"Create inline policy"**
4. **Click "JSON" tab**
5. **Replace the content** with:

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

6. **Click "Next"**
7. **Policy name**: `PW3Mate-ParameterStore-Access`
8. **Click "Create policy"**

---

## 🗃️ **Step 2: Create Parameter Store Entries**

### 2.1 Navigate to Systems Manager

1. **Search for "Systems Manager"** in the AWS search bar
2. **Click "Systems Manager"**
3. **Click "Parameter Store"** in the left sidebar

### 2.2 Create Tesla Credentials Parameters

Create these parameters **one by one**:

**Parameter 1: Client ID**
1. **Click "Create parameter"**
2. **Name**: `/tesla/powerwall/client_id`
3. **Type**: `SecureString`
4. **Value**: Your Tesla Client ID (from Tesla Fleet API setup)
5. **Click "Create parameter"**

**Parameter 2: Client Secret**
1. **Click "Create parameter"**
2. **Name**: `/tesla/powerwall/client_secret`
3. **Type**: `SecureString`
4. **Value**: Your Tesla Client Secret
5. **Click "Create parameter"**

**Parameter 3: Access Token (Placeholder)**
1. **Click "Create parameter"**
2. **Name**: `/tesla/powerwall/access_token`
3. **Type**: `SecureString`
4. **Value**: `placeholder-will-update-later`
5. **Click "Create parameter"**

**Parameter 4: Refresh Token (Placeholder)**
1. **Click "Create parameter"**
2. **Name**: `/tesla/powerwall/refresh_token`
3. **Type**: `SecureString`
4. **Value**: `placeholder-will-update-later`
5. **Click "Create parameter"**

**Parameter 5: Discord Webhook**
1. **Click "Create parameter"**
2. **Name**: `/tesla/powerwall/discord_webhook`
3. **Type**: `SecureString`
4. **Value**: Your Discord webhook URL
5. **Click "Create parameter"**

### 2.3 Verify Parameters

You should now have 5 parameters in Parameter Store:
- `/tesla/powerwall/client_id`
- `/tesla/powerwall/client_secret`
- `/tesla/powerwall/access_token`
- `/tesla/powerwall/refresh_token`
- `/tesla/powerwall/discord_webhook`

---

## ⚡ **Step 3: Create Lambda Functions**

### 3.1 Navigate to Lambda

1. **Search for "Lambda"** in AWS search bar
2. **Click "Lambda"**
3. **Click "Create function"**

### 3.2 Create Token Refresh Function

**Function Configuration:**
1. **Author from scratch**
2. **Function name**: `PW3Mate-Token-Refresh`
3. **Runtime**: `Python 3.11`
4. **Architecture**: `x86_64`
5. **Execution role**: `Use an existing role`
6. **Existing role**: `PW3Mate-Lambda-Role`
7. **Click "Create function"**

**Upload Code:**
1. **Scroll down to "Code source"**
2. **Delete the default code** in `lambda_function.py`
3. **Copy and paste** the token refresh code from [`src/lambda/token_refresh/lambda_function.py`](../../src/lambda/token_refresh/lambda_function.py)
4. **Click "Deploy"**

**Configure Function:**
1. **Click "Configuration" tab**
2. **Click "General configuration"** → **"Edit"**
3. **Timeout**: `1 minute`
4. **Memory**: `256 MB`
5. **Click "Save"**

### 3.3 Create Powerwall Scheduler Function

1. **Go back to Lambda console**
2. **Click "Create function"**

**Function Configuration:**
1. **Author from scratch**
2. **Function name**: `PW3Mate-Powerwall-Scheduler`
3. **Runtime**: `Python 3.11`
4. **Architecture**: `x86_64`
5. **Execution role**: `Use an existing role`
6. **Existing role**: `PW3Mate-Lambda-Role`
7. **Click "Create function"**

**Upload Code:**
1. **Scroll down to "Code source"**
2. **Delete the default code** in `lambda_function.py`
3. **Copy and paste** the scheduler code from [`src/lambda/powerwall_scheduler/lambda_function.py`](../../src/lambda/powerwall_scheduler/lambda_function.py)
4. **Click "Deploy"**

**Configure Function:**
1. **Click "Configuration" tab**
2. **Click "General configuration"** → **"Edit"**
3. **Timeout**: `1 minute`
4. **Memory**: `256 MB`
5. **Click "Save"**

### 3.4 Install Dependencies

Both Lambda functions need the `requests` library. For each function:

1. **Go to function's Code tab**
2. **Click "Layers"** (in the Code source section)
3. **Click "Add a layer"**
4. **Layer source**: `AWS layers`
5. **AWS layers**: Search for `AWSLambda-Python311-SciPy1x` (includes requests)
6. **Version**: Select latest
7. **Click "Add"**

**Alternative: Create deployment package locally**
```bash
# Create folder
mkdir lambda-package
cd lambda-package

# Install requests
pip install requests -t .

# Copy your lambda_function.py
cp ../path/to/lambda_function.py .

# Zip everything
zip -r lambda-function.zip .
```

Then upload the zip file via Lambda console.

---

## ⏰ **Step 4: Create EventBridge Schedules**

### 4.1 Navigate to EventBridge

1. **Search for "EventBridge"** in AWS search bar
2. **Click "EventBridge"**
3. **Click "Rules"** in left sidebar
4. **Click "Create rule"**

### 4.2 Token Refresh Schedule (9 PM)

**Rule Details:**
1. **Name**: `PW3Mate-Token-Refresh-9PM`
2. **Description**: `Daily token refresh at 9 PM UTC`
3. **Rule type**: `Schedule`
4. **Click "Next"**

**Schedule Pattern:**
1. **Schedule pattern**: `Rate-based schedule`
2. **Rate expression**: `cron(0 21 * * ? *)`
3. **Click "Next"**

**Target:**
1. **Target type**: `AWS service`
2. **Service**: `Lambda function`
3. **Function**: `PW3Mate-Token-Refresh`
4. **Click "Next"**

**Review and Create:**
1. **Review settings**
2. **Click "Create rule"**

### 4.3 Backup Token Refresh Schedule (10 PM)

Repeat the above process with:
- **Name**: `PW3Mate-Token-Refresh-10PM`
- **Cron expression**: `cron(0 22 * * ? *)`
- **Target**: `PW3Mate-Token-Refresh`

### 4.4 Powerwall Schedule (11:31 PM → 100%)

**Rule Details:**
1. **Name**: `PW3Mate-Powerwall-2331-100percent`
2. **Description**: `Set Powerwall to 100% at 11:31 PM UTC`
3. **Rule type**: `Schedule`
4. **Click "Next"**

**Schedule Pattern:**
1. **Rate expression**: `cron(31 23 * * ? *)`
2. **Click "Next"**

**Target:**
1. **Target type**: `AWS service`
2. **Service**: `Lambda function`
3. **Function**: `PW3Mate-Powerwall-Scheduler`
4. **Configure target input**: `Constant (JSON text)`
5. **JSON text**:
```json
{
  "backup_reserve_percent": 100,
  "schedule_name": "11:31 PM - Set to 100%"
}
```
6. **Click "Next"**

**Review and Create:**
1. **Review settings**
2. **Click "Create rule"**

### 4.5 Create Remaining Powerwall Schedules

Repeat for each schedule:

**12:29 AM → 0%**
- **Name**: `PW3Mate-Powerwall-0029-0percent`
- **Cron**: `cron(29 0 * * ? *)`
- **JSON**: `{"backup_reserve_percent": 0, "schedule_name": "12:29 AM - Set to 0%"}`

**1:31 AM → 100%**
- **Name**: `PW3Mate-Powerwall-0131-100percent`
- **Cron**: `cron(31 1 * * ? *)`
- **JSON**: `{"backup_reserve_percent": 100, "schedule_name": "1:31 AM - Set to 100%"}`

**5:29 AM → 0%**
- **Name**: `PW3Mate-Powerwall-0529-0percent`
- **Cron**: `cron(29 5 * * ? *)`
- **JSON**: `{"backup_reserve_percent": 0, "schedule_name": "5:29 AM - Set to 0%"}`

---

## 🔗 **Step 5: Grant EventBridge Permissions**

For each Lambda function, grant EventBridge permission to invoke it:

### 5.1 Token Refresh Function Permissions

1. **Go to `PW3Mate-Token-Refresh` Lambda function**
2. **Click "Configuration" tab**
3. **Click "Permissions"** in left sidebar
4. **Click "Add permissions"** → **"Create resource-based policy statement"**
5. **Configuration**:
   - **Service**: `events.amazonaws.com`
   - **Statement ID**: `AllowEventBridgeInvoke`
   - **Principal**: `events.amazonaws.com`
   - **Action**: `lambda:InvokeFunction`
6. **Click "Save"**

### 5.2 Powerwall Scheduler Function Permissions

Repeat the above for `PW3Mate-Powerwall-Scheduler` function.

---

## ✅ **Step 6: Verify Setup**

### 6.1 Check All Components

**IAM Role:**
- ✅ `PW3Mate-Lambda-Role` exists
- ✅ Has `AWSLambdaBasicExecutionRole` permission
- ✅ Has Parameter Store inline policy

**Parameter Store:**
- ✅ 5 parameters created in `/tesla/powerwall/` namespace
- ✅ All are SecureString type

**Lambda Functions:**
- ✅ `PW3Mate-Token-Refresh` created and deployed
- ✅ `PW3Mate-Powerwall-Scheduler` created and deployed
- ✅ Both use `PW3Mate-Lambda-Role`
- ✅ Both have 1-minute timeout and 256MB memory

**EventBridge Rules:**
- ✅ 6 rules created total
- ✅ 2 token refresh schedules (9 PM + 10 PM)
- ✅ 4 Powerwall schedules with correct JSON payloads
- ✅ All rules are enabled

### 6.2 Test Lambda Functions

**Test Token Refresh:**
1. **Go to `PW3Mate-Token-Refresh` function**
2. **Click "Test" tab**
3. **Create new test event**:
   - **Event name**: `manual-test`
   - **Event JSON**: `{}`
4. **Click "Test"**
5. **Check results** - should see success (even with placeholder tokens)

**Test Powerwall Scheduler:**
1. **Go to `PW3Mate-Powerwall-Scheduler` function**
2. **Click "Test" tab**
3. **Create new test event**:
   - **Event name**: `manual-test`
   - **Event JSON**:
   ```json
   {
     "backup_reserve_percent": 50,
     "schedule_name": "Manual Test - Set to 50%"
   }
   ```
4. **Click "Test"**
5. **Check results** - will fail until you have valid tokens, but code should execute

---

## 🔧 **Step 7: Region and Timezone Configuration**

### 7.1 Verify AWS Region

**Important**: All resources should be in the same AWS region!

1. **Check current region** in top-right of AWS Console
2. **Recommended regions**:
   - **US East (N. Virginia)** - `us-east-1`
   - **Europe (Ireland)** - `eu-west-1` 
   - **Asia Pacific (Sydney)** - `ap-southeast-2`

### 7.2 Adjust Schedules for Your Timezone

The example schedules use UTC time. Convert to your timezone:

**US Eastern Time (EST/EDT):**
- Add 5 hours (EST) or 4 hours (EDT) to your desired local time
- Example: 11:31 PM local = 4:31 AM UTC = `cron(31 4 * * ? *)`

**US Pacific Time (PST/PDT):**
- Add 8 hours (PST) or 7 hours (PDT) to your desired local time
- Example: 11:31 PM local = 7:31 AM UTC = `cron(31 7 * * ? *)`

**Australian Eastern Time (AEST/AEDT):**
- Subtract 10 hours (AEST) or 11 hours (AEDT) from your desired local time
- Example: 11:31 PM local = 1:31 PM UTC = `cron(31 13 * * ? *)`

**To Update Schedules:**
1. **Go to EventBridge Rules**
2. **Select a rule** → **Edit**
3. **Update the cron expression**
4. **Click "Update rule"**

---

## 💡 **Step 8: Monitoring and Logs**

### 8.1 Set Up CloudWatch Monitoring

**For each Lambda function:**
1. **Go to function's "Monitoring" tab**
2. **View metrics**:
   - Invocations
   - Duration
   - Errors
   - Success rate

### 8.2 Access Logs

**To view function logs:**
1. **Go to function's "Monitoring" tab**
2. **Click "View CloudWatch logs"**
3. **Click on latest log stream**
4. **Monitor for errors or success messages**

**Log locations:**
- Token Refresh: `/aws/lambda/PW3Mate-Token-Refresh`
- Powerwall Scheduler: `/aws/lambda/PW3Mate-Powerwall-Scheduler`

### 8.3 Set Up Billing Alerts (Optional)

1. **Go to AWS Billing Console**
2. **Create billing alarm** for monthly costs > $1.00
3. **This will alert you if costs exceed expected ~$0.01/month**

---

## 🚨 **Common Issues and Fixes**

### Issue: Lambda function timeout
**Solution**: Increase timeout to 2-3 minutes in function configuration

### Issue: Parameter Store access denied
**Solution**: Verify IAM role has the correct inline policy for Parameter Store

### Issue: EventBridge rule not triggering
**Solution**: 
- Check if rule is enabled
- Verify cron expression syntax
- Ensure Lambda has resource-based policy allowing EventBridge

### Issue: Missing `requests` module
**Solution**: Add AWS layer or create deployment package with dependencies

### Issue: Wrong timezone
**Solution**: Recalculate cron expressions for your timezone using UTC

---

## 🔒 **Security Best Practices**

### 8.1 IAM Role Security
- ✅ Use least-privilege permissions
- ✅ Only grant access to `/tesla/powerwall/*` parameters
- ✅ Regular review of role permissions

### 8.2 Parameter Store Security
- ✅ All sensitive data stored as SecureString
- ✅ Use AWS KMS encryption (default)
- ✅ Never log parameter values in CloudWatch

### 8.3 Lambda Security
- ✅ No hardcoded credentials in function code
- ✅ Use VPC endpoints if in VPC (optional)
- ✅ Enable function-level concurrency limits

---

## 💰 **Cost Optimization**

### 8.1 Expected Monthly Costs

**Typical usage (6 executions/day):**
- **Lambda requests**: 180/month = $0.0000036
- **Lambda compute**: ~30 seconds total = $0.0000050
- **Parameter Store**: Free tier covers usage
- **EventBridge**: Free tier covers usage
- **Total**: **~$0.01/month**

### 8.2 Cost Monitoring

**Set up cost alerts:**
1. **AWS Budgets** → **Create budget**
2. **Budget type**: Cost budget
3. **Amount**: $1.00/month
4. **Alert threshold**: 80% of budget

---

## 📋 **Deployment Checklist**

Before proceeding to token generation:

**IAM & Security:**
- [ ] IAM role created with correct permissions
- [ ] Parameter Store inline policy attached
- [ ] All parameters created and populated

**Lambda Functions:**
- [ ] Both functions created and deployed
- [ ] Correct IAM role attached
- [ ] Timeout set to 1+ minutes
- [ ] Dependencies installed (requests library)
- [ ] Test executions successful

**EventBridge:**
- [ ] 6 rules created (2 token refresh + 4 Powerwall)
- [ ] Correct cron expressions for your timezone
- [ ] JSON payloads configured correctly
- [ ] Rules are enabled
- [ ] Lambda permissions granted to EventBridge

**Monitoring:**
- [ ] CloudWatch logs accessible
- [ ] Billing alerts configured
- [ ] Region confirmed and consistent

---

## 🎯 **What's Next?**

Your AWS infrastructure is now ready! Next steps:

1. **[Generate Tesla OAuth Tokens](05-token-generation.md)** - Get real access/refresh tokens
2. **[Test the Complete System](06-testing-deployment.md)** - Verify everything works
3. **[Monitor and Maintain](../troubleshooting.md)** - Keep your system running

**Current Status:**
- ✅ AWS infrastructure deployed
- ✅ Lambda functions ready
- ✅ EventBridge schedules configured
- ⏳ Need Tesla OAuth tokens (next step)

---

## 🔗 **Related Resources**

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)
- [AWS Parameter Store Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [Cron Expression Generator](https://crontab.cronhub.io/)

---

**✅ Your AWS infrastructure is ready for Tesla Powerwall automation!**

**Next Step**: [Generate Tesla OAuth Tokens →](05-token-generation.md)