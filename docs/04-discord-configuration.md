# Discord Configuration for PW3Mate

Set up beautiful, informative notifications for your Tesla Powerwall automation system using Discord webhooks.

## 🎯 **What You'll Get**

Rich, formatted notifications showing:
- ✅ Backup reserve changes with old/new percentages
- 📊 Live Powerwall status (battery level, solar, home usage)
- ⚡ Power flow data (charging/discharging)
- 🕐 Timestamp and schedule information
- 🚨 Error alerts and system status

**Time Required:** 5 minutes

---

## 📱 **Step 1: Create Discord Server (if needed)**

### 1.1 Create New Server

If you don't have a Discord server for notifications:

1. **Open Discord** (web, desktop, or mobile app)
2. **Click the "+" icon** on the left sidebar
3. **Select "Create My Own"**
4. **Choose "For me and my friends"**
5. **Server name**: `Tesla Powerwall` (or your preferred name)
6. **Upload server icon** (optional): Tesla or battery emoji
7. **Click "Create"**

### 1.2 Create Dedicated Channel (Recommended)

1. **Right-click your server name**
2. **Select "Create Channel"**
3. **Channel type**: `Text`
4. **Channel name**: `powerwall-alerts` or `tesla-notifications`
5. **Make private**: Optional (recommended for personal use)
6. **Click "Create Channel"**

---

## 🔗 **Step 2: Create Webhook**

### 2.1 Access Server Settings

1. **Right-click your server name** (in server list)
2. **Select "Server Settings"**
3. **Click "Integrations"** in the left sidebar
4. **Click "Webhooks"**

### 2.2 Create New Webhook

1. **Click "Create Webhook"**
2. **Configure webhook**:
   - **Name**: `Tesla Powerwall Bot`
   - **Channel**: Select your notification channel (e.g., `#powerwall-alerts`)
   - **Avatar**: Upload a Tesla/battery icon (optional)

### 2.3 Copy Webhook URL

1. **Click "Copy Webhook URL"**
2. **Save the URL securely** - it looks like:
   ```
   https://discord.com/api/webhooks/123456789012345678/abcdef...
   ```

⚠️ **Important**: Keep this URL private! Anyone with it can send messages to your Discord server.

---

## 🧪 **Step 3: Test Webhook**

### 3.1 Test with curl (Optional)

If you have curl available:

```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "embeds": [{
      "title": "🔋 Tesla Powerwall Test",
      "description": "Testing Discord integration for PW3Mate",
      "color": 65280,
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
    }]
  }'
```

### 3.2 Test with Python (Optional)

```python
import requests
from datetime import datetime

webhook_url = "YOUR_WEBHOOK_URL"

data = {
    "embeds": [{
        "title": "🔋 Tesla Powerwall Test",
        "description": "Testing Discord integration for PW3Mate",
        "color": 0x00ff00,  # Green
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "PW3Mate Test"
        }
    }]
}

response = requests.post(webhook_url, json=data)
print(f"Status: {response.status_code}")
```

### 3.3 Expected Result

You should see a test message in your Discord channel with:
- Green colored embed
- Title: "🔋 Tesla Powerwall Test"
- Timestamp
- Clean formatting

---

## ⚙️ **Step 4: Configure AWS Parameter Store**

### 4.1 Store Webhook URL

1. **Go to [AWS Systems Manager](https://console.aws.amazon.com/systems-manager/)**
2. **Click "Parameter Store"**
3. **Find parameter**: `/tesla/powerwall/discord_webhook`
4. **Click "Edit"**
5. **Update value** with your Discord webhook URL
6. **Click "Save changes"**

### 4.2 Verify Parameter

Ensure the parameter exists and has the correct value:
- **Name**: `/tesla/powerwall/discord_webhook`
- **Type**: `SecureString`
- **Value**: `https://discord.com/api/webhooks/...`

---

## 📊 **Step 5: Notification Examples**

### 5.1 Successful Schedule Change

```
✅ Tesla Powerwall Updated
11:31 PM - Set to 100%

Backup reserve changed: 50% → 100%

📊 Current Status:
🔋 Battery: 85%
⚡ Battery Power: -2.1kW (charging)
☀️ Solar: 0W
🏠 Home Usage: 1.8kW
```

### 5.2 Daily Token Refresh

```
🔋 Daily Tesla Token Refresh
✅ Tesla Token Refresh Successful

🕘 Time: 9:00 PM UTC
🔄 New tokens generated and stored
⏰ Access token valid until: 5:00 AM UTC
📅 Refresh token valid for: 3 months

🔋 Ready for tonight's Powerwall schedule:
• 11:31 PM → 100%
• 12:29 AM → 0%
• 1:31 AM → 100%
• 5:29 AM → 0%

📊 All systems operational ✅
```

### 5.3 Error Alert

```
🚨 Tesla Token EMERGENCY
🚨 URGENT: Tesla Token Emergency

Daily token refresh failed: Refresh token is expired or invalid

IMPACT: Tonight's Powerwall schedule will NOT work!
• 11:31 PM → 100% ❌
• 12:29 AM → 0% ❌
• 1:31 AM → 100% ❌
• 5:29 AM → 0% ❌

ACTION REQUIRED:
1. Generate new tokens via OAuth flow
2. Update Parameter Store
3. System will resume automatically
```

---

## 🎨 **Step 6: Customize Notifications (Optional)**

### 6.1 Discord Embed Colors

The system uses color-coded notifications:
- 🟢 **Green** (`0x00ff00`): Success, normal operations
- 🔴 **Red** (`0xff0000`): Critical errors, urgent attention needed
- 🟠 **Orange** (`0xffa500`): Warnings, temporary issues
- 🟣 **Purple** (`0x800080`): System crashes, unexpected errors

### 6.2 Custom Bot Name and Avatar

1. **Go back to webhook settings** in Discord
2. **Change name** to your preference:
   - `Tesla Bot`
   - `Powerwall Assistant`
   - `Energy Manager`
3. **Upload custom avatar**:
   - Tesla logo
   - Battery icon
   - Lightning bolt
   - Custom image

### 6.3 Notification Frequency

By default, you'll receive notifications for:
- ✅ **Every schedule change** (4 times daily)
- ✅ **Daily token refresh** (2 times daily)
- ✅ **Errors and warnings** (as needed)

To reduce notifications, you can modify the Lambda function code to:
- Only notify on errors
- Daily summary instead of individual changes
- Weekly status reports

---

## 📱 **Step 7: Mobile Notifications**

### 7.1 Discord Mobile App

1. **Install Discord mobile app**
2. **Join your server**
3. **Enable push notifications**:
   - Settings → Notifications
   - Allow notifications for your server
   - Customize notification types

### 7.2 Notification Settings

Configure Discord notifications:
- **All messages**: Get notified for every Powerwall update
- **Only @mentions**: Only get notified for critical errors
- **Nothing**: Silent notifications (check manually)

**Recommended**: Use "All messages" for the Powerwall channel since notifications are infrequent but important.

---

## 🔧 **Troubleshooting**

### Issue: No notifications appearing
**Solutions:**
- ✅ Verify webhook URL is correct in Parameter Store
- ✅ Check Discord channel permissions
- ✅ Test webhook manually with curl
- ✅ Check Lambda function logs for errors

### Issue: Notifications look plain/unformatted
**Solutions:**
- ✅ Ensure using embeds (not plain text)
- ✅ Check JSON formatting in webhook payload
- ✅ Verify Discord client supports rich embeds

### Issue: Too many notifications
**Solutions:**
- ✅ Create separate channel for Powerwall notifications
- ✅ Adjust Discord notification settings
- ✅ Modify Lambda function to reduce notification frequency

### Issue: Webhook expired or not working
**Solutions:**
- ✅ Regenerate webhook in Discord server settings
- ✅ Update Parameter Store with new webhook URL
- ✅ Test new webhook before deploying

---

## 🔒 **Security Best Practices**

### 7.1 Webhook Security

**✅ DO:**
- Keep webhook URL private and secure
- Use a dedicated server/channel for notifications
- Regularly review server members and permissions
- Enable Discord 2FA for your account

**❌ DON'T:**
- Share webhook URL publicly
- Use webhooks in public servers
- Post webhook URLs in documentation or code
- Grant unnecessary permissions to server members

### 7.2 Information Security

**Notifications may contain:**
- ✅ Powerwall status and power levels (generally safe)
- ✅ Schedule information (timing patterns)
- ❌ Never contain: credentials, tokens, or sensitive data

**Privacy considerations:**
- Energy usage patterns may indicate home occupancy
- Consider who has access to your Discord server
- Use private servers for personal notifications

---

## 📋 **Configuration Checklist**

Before proceeding to the next setup step:

**Discord Setup:**
- [ ] Discord server created or selected
- [ ] Dedicated channel created for notifications
- [ ] Webhook created and configured
- [ ] Webhook URL copied securely
- [ ] Test message sent successfully

**AWS Configuration:**
- [ ] Webhook URL stored in Parameter Store
- [ ] Parameter path is `/tesla/powerwall/discord_webhook`
- [ ] Parameter type is `SecureString`
- [ ] Parameter value starts with `https://discord.com/api/webhooks/`

**Testing:**
- [ ] Manual webhook test successful
- [ ] Discord notifications appearing in correct channel
- [ ] Formatting and colors working correctly
- [ ] Mobile notifications working (if desired)

---

## 🎯 **What's Next?**

Your Discord notifications are now configured! You'll start receiving beautiful, informative notifications once your Tesla tokens are set up and the system is running.

**Next Steps:**
1. **[Generate Tesla OAuth Tokens](05-token-generation.md)** - Get API access
2. **[Test the Complete System](06-testing-deployment.md)** - Verify everything works
3. **Enjoy automated notifications** about your Powerwall!

**Expected Notifications:**
- 🕘 **Daily token refresh**: 2 notifications per day (9 PM & 10 PM UTC)
- 🔋 **Powerwall changes**: 4 notifications per day (schedule dependent)
- 🚨 **Error alerts**: Only when issues occur

---

**✅ Discord notifications are ready for your Tesla Powerwall automation!**

**Next Step**: [Generate Tesla OAuth Tokens →](05-token-generation.md)