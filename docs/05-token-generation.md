# Tesla OAuth Token Generation

Generate the access and refresh tokens needed for your Powerwall automation system to communicate with Tesla's Fleet API.

## 🎯 **What You'll Get**

- Access token (valid for 8 hours)
- Refresh token (valid for 3 months, renewable)
- Working authentication for Tesla Fleet API
- Foundation for automated token refresh

**Time Required:** 15 minutes

---

## 📋 **Prerequisites**

- ✅ Tesla Fleet API setup complete
- ✅ AWS infrastructure deployed
- ✅ Discord notifications configured
- ✅ Tesla Client ID and Client Secret
- ✅ Your GitHub domain (e.g., `yourusername.github.io`)

---

## 🔐 **Step 1: Build Authorization URL**

### 1.1 Construct OAuth URL

Replace the placeholders with your actual values:

```
https://auth.tesla.com/oauth2/v3/authorize?client_id=YOUR_CLIENT_ID&locale=en-US&prompt=login&redirect_uri=https://YOUR_DOMAIN/oauth/callback&response_type=code&scope=openid%20energy_device_data%20energy_cmds%20offline_access&state=pw3mate2025
```

**Replace:**
- `YOUR_CLIENT_ID` → Your Tesla Client ID
- `YOUR_DOMAIN` → Your GitHub domain (e.g., `yourusername.github.io`)

**Example URL:**
```
https://auth.tesla.com/oauth2/v3/authorize?client_id=8f2a9b47-d3e1-4c56-a789-1b2c3d4e5f6g&locale=en-US&prompt=login&redirect_uri=https://johnsmith.github.io/oauth/callback&response_type=code&scope=openid%20energy_device_data%20energy_cmds%20offline_access&state=pw3mate2025
```

### 1.2 URL Parameters Explained

- **client_id**: Your Tesla application Client ID
- **redirect_uri**: Must match your registered redirect URI exactly
- **response_type**: `code` for authorization code flow
- **scope**: Permissions your app needs
- **state**: Random string to prevent CSRF attacks
- **prompt**: `login` to ensure fresh authentication

---

## 🌐 **Step 2: Complete User Authorization**

### 2.1 Open Authorization URL

1. **Copy your authorization URL** from Step 1
2. **Open in a web browser** (preferably incognito/private mode)
3. **You'll be redirected to Tesla's login page**

### 2.2 Tesla Login

1. **Enter your Tesla credentials**:
   - Email: Same as Tesla mobile app
   - Password: Same as Tesla mobile app
2. **Complete 2FA** if enabled (recommended)
3. **Tesla will show authorization page**

### 2.3 Grant Permissions

**Tesla will show:**
```
PW3Mate Powerwall Automation wants to:
✓ Read your energy device data
✓ Send commands to your energy devices
✓ Maintain access when you're not present
✓ Access basic profile information

This will allow the application to:
- View your Powerwall status and settings
- Change backup reserve percentage
- Read energy flow and battery data
- Continue working when you're offline
```

**Click "Allow"** to grant permissions.

### 2.4 Capture Authorization Code

**After clicking "Allow", you'll be redirected to:**
```
https://yourusername.github.io/oauth/callback?code=AUTHORIZATION_CODE&state=pw3mate2025
```

**Important Steps:**
1. **The page will show an error** (404 or similar) - this is expected!
2. **Copy the authorization code** from the URL
3. **The code looks like**: `NA_abc123def456ghi789...`
4. **Save it temporarily** - you'll use it in the next step

**Example:**
```
URL: https://johnsmith.github.io/oauth/callback?code=NA_xyz789abc123def456ghi789jkl012mno345&state=pw3mate2025

Authorization Code: NA_xyz789abc123def456ghi789jkl012mno345
```

---

## 🔄 **Step 3: Exchange Code for Tokens**

### 3.1 Prepare Token Request

**Using curl (Mac/Linux/WSL):**
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

**Using PowerShell (Windows):**
```powershell
$body = @{
    grant_type = 'authorization_code'
    client_id = 'YOUR_CLIENT_ID'
    client_secret = 'YOUR_CLIENT_SECRET'
    code = 'YOUR_AUTHORIZATION_CODE'
    audience = 'https://fleet-api.prd.eu.vn.cloud.tesla.com'
    redirect_uri = 'https://YOUR_DOMAIN/oauth/callback'
}

$response = Invoke-RestMethod -Uri 'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token' -Method Post -Body $body
$response | ConvertTo-Json -Depth 3
```

### 3.2 Replace Placeholders

**Replace in the command:**
- `YOUR_CLIENT_ID` → Your Tesla Client ID
- `YOUR_CLIENT_SECRET` → Your Tesla Client Secret
- `YOUR_AUTHORIZATION_CODE` → Code from Step 2.4
- `YOUR_DOMAIN` → Your GitHub domain

### 3.3 Execute Token Request

**Expected Successful Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik...",
  "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik...",
  "expires_in": 28800,
  "token_type": "Bearer",
  "scope": "openid energy_device_data energy_cmds offline_access"
}
```

**Important Fields:**
- **access_token**: Used for API calls (valid 8 hours)
- **refresh_token**: Used to get new access tokens (valid 3 months)
- **expires_in**: 28800 seconds = 8 hours

---

## 🗃️ **Step 4: Store Tokens in AWS Parameter Store**

### 4.1 Navigate to Parameter Store

1. **Go to [AWS Systems Manager](https://console.aws.amazon.com/systems-manager/)**
2. **Click "Parameter Store"**
3. **Find your Tesla parameters**

### 4.2 Update Access Token

1. **Click on `/tesla/powerwall/access_token`**
2. **Click "Edit"**
3. **Replace the value** with your access token from Step 3
4. **Keep as SecureString**
5. **Click "Save changes"**

### 4.3 Update Refresh Token

1. **Click on `/tesla/powerwall/refresh_token`**
2. **Click "Edit"**
3. **Replace the value** with your refresh token from Step 3
4. **Keep as SecureString**
5. **Click "Save changes"**

### 4.4 Verify Parameter Store

**Your Parameter Store should now have:**
```
/tesla/powerwall/client_id         → Your Client ID
/tesla/powerwall/client_secret     → Your Client Secret
/tesla/powerwall/access_token      → eyJhbGciOiJSUzI1NiIs... (from OAuth)
/tesla/powerwall/refresh_token     → eyJhbGciOiJSUzI1NiIs... (from OAuth)
/tesla/powerwall/discord_webhook   → https://discord.com/api/webhooks/...
```

---

## 🧪 **Step 5: Test API Access**

### 5.1 Test Token Refresh Lambda

1. **Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)**
2. **Click on `PW3Mate-Token-Refresh` function**
3. **Click "Test" tab**
4. **Create test event**:
   - **Event name**: `manual-test`
   - **Event JSON**: `{}`
5. **Click "Test"**

**Expected Success Response:**
```json
{
  "statusCode": 200,
  "body": "{\"status\":\"success\",\"message\":\"Daily token refresh completed\",\"tokens_updated\":true,\"timestamp\":\"2025-01-01T12:00:00.000Z\"}"
}
```

**Check Discord:** You should receive a green notification about successful token refresh.

### 5.2 Test Powerwall Scheduler Lambda

1. **Go to `PW3Mate-Powerwall-Scheduler` function**
2. **Click "Test" tab**
3. **Create test event**:
   - **Event name**: `manual-test`
   - **Event JSON**:
   ```json
   {
     "backup_reserve_percent": 75,
     "schedule_name": "Manual Test - Set to 75%"
   }
   ```
4. **Click "Test"**

**Expected Success Response:**
```json
{
  "statusCode": 200,
  "body": "{\"message\":\"Successfully set backup reserve to 75%\",\"site_id\":\"12345\",\"backup_reserve\":75,\"schedule_name\":\"Manual Test - Set to 75%\",\"old_reserve\":50,\"timestamp\":\"2025-01-01T12:00:00.000Z\"}"
}
```

**Check Tesla App:** Your Powerwall backup reserve should change to 75%.

**Check Discord:** You should receive a notification with live Powerwall data.

---

## 📱 **Step 6: Verify Tesla App Changes**

### 6.1 Open Tesla Mobile App

1. **Open Tesla app** on your phone
2. **Navigate to Energy** → **Your Powerwall**
3. **Check "Backup Reserve"** setting
4. **Should show 75%** (from test in Step 5.2)

### 6.2 Expected Changes

**You should see:**
- ✅ Backup reserve changed to 75%
- ✅ Change timestamp updated
- ✅ Battery status information
- ✅ Power flow data (if available)

### 6.3 Reset to Desired Level (Optional)

**To reset to your preferred backup reserve:**
1. **Run the Powerwall test again** with your preferred percentage
2. **Or manually change in Tesla app**
3. **Your automation will take over** according to schedule

---

## 🕐 **Step 7: Understand Token Lifecycle**

### 7.1 Token Validity

**Access Token:**
- ✅ **Valid for**: 8 hours
- ✅ **Used for**: All API calls
- ✅ **Automatically refreshed**: Daily at 9 PM and 10 PM UTC

**Refresh Token:**
- ✅ **Valid for**: 3 months
- ✅ **Used for**: Getting new access tokens
- ✅ **Renewed when**: Daily refresh creates new refresh token

### 7.2 Automatic Refresh System

**Your system includes:**
- 🕘 **Primary refresh**: 9:00 PM UTC daily
- 🛡️ **Backup refresh**: 10:00 PM UTC daily
- 🔄 **Emergency refresh**: Before each Powerwall command (if needed)

**This ensures:**
- ✅ Tokens never expire
- ✅ System runs continuously
- ✅ No manual intervention required

---

## 🐛 **Troubleshooting**

### Common Issues

**Q: Authorization code expired**
- **A**: Authorization codes expire quickly (10 minutes)
- **A**: Restart from Step 1 with a fresh authorization URL
- **A**: Complete the process faster once you get the code

**Q: Invalid client credentials**
- **A**: Verify Client ID and Client Secret are correct
- **A**: Ensure no extra spaces or characters
- **A**: Check that application is approved (not just submitted)

**Q: Redirect URI mismatch**
- **A**: Ensure redirect URI exactly matches registered URI
- **A**: Check for www vs non-www differences
- **A**: Verify https vs http protocol

**Q: Lambda test fails with token error**
- **A**: Verify tokens are stored correctly in Parameter Store
- **A**: Check token format (should start with "eyJ")
- **A**: Ensure Parameter Store permissions are correct

**Q: Powerwall doesn't change**
- **A**: Check Tesla app for error messages
- **A**: Verify Powerwall is online and operational
- **A**: Ensure you have the correct energy site permissions

### Token Format Validation

**Valid tokens start with:**
- **Access Token**: `eyJhbGciOiJSUzI1NiIs...`
- **Refresh Token**: `eyJhbGciOiJSUzI1NiIs...`

**Invalid tokens:**
- Start with anything else
- Contain obvious placeholder text
- Are too short (< 100 characters)
- Have spaces or newlines

---

## 🔒 **Security Notes**

### 7.1 Token Security

**✅ DO:**
- Store tokens only in AWS Parameter Store (SecureString)
- Never log or display full tokens
- Rotate tokens if compromised
- Monitor for unauthorized usage

**❌ DON'T:**
- Store tokens in plain text
- Share tokens publicly
- Use tokens outside of your automation
- Leave tokens in browser history

### 7.2 Access Monitoring

**Monitor for:**
- Unexpected API calls
- Changes you didn't authorize
- Login notifications from Tesla
- Unusual energy usage patterns

**If you suspect compromise:**
1. **Revoke application access** in Tesla Developer Portal
2. **Generate new tokens** through OAuth flow
3. **Update Parameter Store** with new tokens
4. **Review recent API activity**

---

## 📋 **Completion Checklist**

Before proceeding to testing:

**OAuth Flow Complete:**
- [ ] Authorization URL built correctly
- [ ] Tesla login and authorization completed
- [ ] Authorization code captured from callback URL
- [ ] Token exchange successful

**AWS Integration:**
- [ ] Access token stored in Parameter Store
- [ ] Refresh token stored in Parameter Store
- [ ] Token refresh Lambda test successful
- [ ] Powerwall scheduler Lambda test successful

**Tesla Integration:**
- [ ] Powerwall backup reserve changed via test
- [ ] Tesla app shows updated backup reserve
- [ ] No error messages in Tesla app
- [ ] API calls working correctly

**Notifications:**
- [ ] Discord notifications received for token refresh
- [ ] Discord notifications received for Powerwall changes
- [ ] Notification formatting correct and readable

---

## 🎯 **What's Next?**

Your OAuth tokens are now working! Next steps:

1. **[Testing & Deployment](06-testing-deployment.md)** - Comprehensive system testing
2. **Monitor your first automated schedule** - Watch it work overnight
3. **Customize schedules** - Adjust for your electricity rates and usage

**Current Status:**
- ✅ Tesla Fleet API registered
- ✅ AWS infrastructure deployed
- ✅ Discord notifications configured
- ✅ OAuth tokens working
- ⏳ Ready for comprehensive testing (next step)

---

## 🔗 **Related Resources**

- [Tesla OAuth 2.0 Documentation](https://developer.tesla.com/docs/fleet-api/authentication)
- [Tesla Fleet API Reference](https://developer.tesla.com/docs/fleet-api/reference)
- [AWS Parameter Store Best Practices](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-securestring.html)

---

**✅ OAuth tokens generated and working! Ready for comprehensive testing.**

**Next Step**: [Testing & Deployment →](06-testing-deployment.md)