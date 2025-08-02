# Tesla Fleet API Setup

Register your application with Tesla's Fleet API to get the credentials needed for Powerwall automation.

## 🎯 **What You'll Get**

- Tesla Client ID and Client Secret
- Registered application for Fleet API access
- Partner account registration
- Foundation for OAuth token generation

**Time Required:** 20 minutes (plus 1-3 days for Tesla approval)

---

## 📋 **Prerequisites**

- Tesla account (same as Tesla mobile app)
- Tesla Powerwall 3 installed and operational
- Domain setup from [GitHub Domain Setup](02-github-domain-setup.md)
- Access to your domain's `.well-known` directory

---

## 🚗 **Step 1: Tesla Developer Account Registration**

### 1.1 Create Developer Account

1. **Go to [Tesla Developer Portal](https://developer.tesla.com/)**
2. **Click "Get Started"** or "Sign In"
3. **Sign in** with your Tesla account credentials
   - Use the same email/password as your Tesla mobile app
   - Complete 2FA if prompted
4. **Accept Developer Terms** of Service
5. **Complete developer profile** if prompted

### 1.2 Verify Account Access

After signing in, you should see:
- Developer dashboard
- "Create New App" option
- Documentation links
- API reference materials

---

## 📱 **Step 2: Create Application**

### 2.1 Start Application Creation

1. **Click "Create New App"** from the developer dashboard
2. **Choose application type**: `Third-party`

### 2.2 Fill Application Details

**Basic Information:**
- **Application Name**: `PW3Mate Powerwall Automation`
- **Description**: `Automated backup reserve scheduling for personal Tesla Powerwall using AWS Lambda`
- **Organization** (optional): Your name or company
- **Website URL**: `https://yourusername.github.io` (from GitHub domain setup)

**Technical Configuration:**
- **Redirect URIs**: `https://yourusername.github.io/oauth/callback`
- **Allowed Origins**: `https://yourusername.github.io`

**Permissions (Scopes):**
Select these scopes:
- ✅ `openid` - Basic authentication
- ✅ `offline_access` - Refresh token access
- ✅ `energy_device_data` - Read Powerwall data
- ✅ `energy_cmds` - Control Powerwall settings

**Application Purpose:**
```
Personal automation system for Tesla Powerwall backup reserve scheduling.
The application will:
- Read current Powerwall status and settings
- Adjust backup reserve percentage on a schedule
- Optimize energy usage for time-of-use electricity rates
- Send notifications about changes and system status

This is for personal use only with my own Tesla Powerwall.
```

### 2.3 Submit Application

1. **Review all information** carefully
2. **Click "Submit Application"**
3. **Note the application ID** if shown

---

## ⏳ **Step 3: Wait for Approval**

### 3.1 Approval Timeline

**Typical Timeline:**
- ✅ **Personal/hobby applications**: 1-3 business days
- ⏳ **Commercial applications**: 1-2 weeks
- 🚨 **Complex applications**: 2-4 weeks

### 3.2 Approval Notification

You'll receive notification via:
- Email to your Tesla account email
- Dashboard update in Tesla Developer Portal
- Status change from "Under Review" to "Approved"

### 3.3 While Waiting

**You can:**
- Continue with AWS infrastructure setup
- Set up Discord notifications
- Prepare your development environment

**You cannot:**
- Generate OAuth tokens (requires approval)
- Test API calls
- Complete the system deployment

---

## 🔑 **Step 4: Get Your Credentials (After Approval)**

### 4.1 Access Approved Application

1. **Sign in to [Tesla Developer Portal](https://developer.tesla.com/)**
2. **Go to your applications** (dashboard)
3. **Click on your approved application**

### 4.2 Copy Credentials

**You'll see:**
- **Client ID**: Long UUID format (e.g., `8f2a9b47-d3e1-4c56-a789-1b2c3d4e5f6g`)
- **Client Secret**: Starts with `ta-secret.` (e.g., `ta-secret.Kx9Zm4Pq7Nv2RtY8...`)

**Important:**
- ✅ Copy both credentials to a secure location
- ✅ Keep the Client Secret private and secure
- ✅ You'll need these for AWS Parameter Store setup

### 4.3 Save Credentials Securely

**Recommended storage:**
- Password manager (1Password, Bitwarden, etc.)
- Encrypted notes app
- Secure text file (not in Git repository)

**Format for saving:**
```
Tesla Fleet API Credentials - PW3Mate
=====================================
Client ID: 8f2a9b47-d3e1-4c56-a789-1b2c3d4e5f6g
Client Secret: ta-secret.Kx9Zm4Pq7Nv2RtY8...
Application: PW3Mate Powerwall Automation
Domain: https://yourusername.github.io
Created: [Date]
```

---

## 🔐 **Step 5: Register Partner Account**

### 5.1 Generate Partner Authentication Token

**Using curl (Mac/Linux/WSL):**
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

**Using PowerShell (Windows):**
```powershell
$body = @{
    grant_type = 'client_credentials'
    client_id = 'YOUR_CLIENT_ID'
    client_secret = 'YOUR_CLIENT_SECRET'
    scope = 'openid energy_device_data energy_cmds offline_access'
    audience = 'https://fleet-api.prd.eu.vn.cloud.tesla.com'
}

$response = Invoke-RestMethod -Uri 'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token' -Method Post -Body $body
$response.access_token
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 5.2 Register Your Domain

**Using curl:**
```bash
curl -H "Authorization: Bearer YOUR_PARTNER_TOKEN" \
     -H 'Content-Type: application/json' \
     --data '{"domain": "yourusername.github.io"}' \
     -X POST \
     -i https://fleet-api.prd.eu.vn.cloud.tesla.com/api/1/partner_accounts
```

**Using PowerShell:**
```powershell
$headers = @{
    'Authorization' = 'Bearer YOUR_PARTNER_TOKEN'
    'Content-Type' = 'application/json'
}

$body = @{
    domain = 'yourusername.github.io'
} | ConvertTo-Json

Invoke-RestMethod -Uri 'https://fleet-api.prd.eu.vn.cloud.tesla.com/api/1/partner_accounts' -Method Post -Headers $headers -Body $body
```

**Expected Response:**
```json
{
  "response": {
    "domain": "yourusername.github.io",
    "public_key": "-----BEGIN PUBLIC KEY-----\n...",
    "registered_at": "2025-01-01T12:00:00Z"
  }
}
```

---

## ✅ **Step 6: Verify Setup**

### 6.1 Verify Public Key Access

**Test that Tesla can access your public key:**
```bash
curl https://yourusername.github.io/.well-known/appspecific/com.tesla.3p.public-key.pem
```

**Should return your public key:**
```
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
-----END PUBLIC KEY-----
```

### 6.2 Test Partner Authentication

**Verify partner registration:**
```bash
curl -H "Authorization: Bearer YOUR_PARTNER_TOKEN" \
     https://fleet-api.prd.eu.vn.cloud.tesla.com/api/1/partner_accounts
```

**Should return your domain registration:**
```json
{
  "response": [
    {
      "domain": "yourusername.github.io",
      "registered_at": "2025-01-01T12:00:00Z"
    }
  ]
}
```

---

## 🐛 **Troubleshooting**

### Common Issues

**Q: Application rejected or taking too long**
- **A**: Ensure description is clear about personal use
- **A**: Verify domain is accessible and has correct public key
- **A**: Check that all required scopes are selected
- **A**: Be patient - Tesla approval can take several days

**Q: Public key not accessible**
- **A**: Verify GitHub Pages is enabled and deployed
- **A**: Check exact file path: `.well-known/appspecific/com.tesla.3p.public-key.pem`
- **A**: Ensure file contains valid EC public key format
- **A**: Wait 10-15 minutes for GitHub Pages deployment

**Q: Partner registration fails**
- **A**: Verify partner token is valid and not expired
- **A**: Check domain matches exactly (no www, no trailing slash)
- **A**: Ensure public key is accessible at the required path
- **A**: Try using different API endpoint (US vs EU)

**Q: Client credentials not showing**
- **A**: Ensure application is fully approved (not just submitted)
- **A**: Check application status in developer portal
- **A**: Try refreshing browser or signing out/in
- **A**: Contact Tesla developer support if persistent

### Regional Considerations

**API Endpoints by Region:**
- **North America**: `fleet-api.prd.na.vn.cloud.tesla.com`
- **Europe**: `fleet-api.prd.eu.vn.cloud.tesla.com`
- **Asia-Pacific**: `fleet-api.prd.apac.vn.cloud.tesla.com`

**Choose the endpoint closest to your Tesla account region.**

---

## 🔒 **Security Best Practices**

### 6.1 Credential Security

**✅ DO:**
- Store credentials in a password manager
- Use secure, encrypted storage
- Keep credentials private and confidential
- Regularly review application access

**❌ DON'T:**
- Share credentials publicly
- Store in plain text files
- Commit to version control
- Use for unauthorized purposes

### 6.2 Application Security

**✅ DO:**
- Use the minimum required scopes
- Keep your domain secure
- Monitor for unusual API usage
- Follow Tesla's API usage guidelines

**❌ DON'T:**
- Request unnecessary permissions
- Allow unauthorized domain access
- Exceed API rate limits
- Use for commercial purposes without proper approval

---

## 📝 **What You Should Have Now**

After completing this step:

**✅ Tesla Developer Account**
- Registered and verified
- Access to developer portal

**✅ Approved Application**
- Application approved by Tesla
- Client ID and Client Secret obtained

**✅ Partner Registration**
- Domain registered with Tesla
- Public key verification successful

**✅ Credentials Secured**
- Client ID saved securely
- Client Secret stored safely
- Ready for AWS Parameter Store

---

## 🎯 **What's Next?**

Your Tesla Fleet API setup is complete! Next steps:

1. **[AWS Infrastructure Setup](03-aws-infrastructure-setup.md)** - Deploy Lambda functions and EventBridge
2. **[Discord Configuration](04-discord-configuration.md)** - Set up notifications
3. **[Token Generation](05-token-generation.md)** - Complete OAuth flow for API access

**Current Status:**
- ✅ Tesla Fleet API registered
- ✅ Domain verification complete
- ✅ Partner account registered
- ⏳ Need AWS infrastructure (next step)

---

## 🔗 **Related Resources**

- [Tesla Fleet API Documentation](https://developer.tesla.com/docs/fleet-api)
- [Tesla OAuth 2.0 Guide](https://developer.tesla.com/docs/fleet-api/authentication)
- [Tesla API Rate Limits](https://developer.tesla.com/docs/fleet-api/getting-started/rate-limits)
- [Tesla Developer Support](https://developer.tesla.com/support)

---

**✅ Tesla Fleet API setup complete! Ready for AWS infrastructure deployment.**

**Next Step**: [AWS Infrastructure Setup →](03-aws-infrastructure-setup.md)