# PW3Mate - Complete Setup Guide

This comprehensive guide will walk you through setting up fully automated Tesla Powerwall backup reserve scheduling from start to finish.

## 🎯 **What You'll Build**

By the end of this guide, you'll have:
- ✅ Automated Powerwall backup reserve scheduling (4 times daily)
- ✅ Dual token refresh system (9 PM + 10 PM UTC for reliability)
- ✅ Beautiful Discord notifications for all operations
- ✅ Enterprise-grade security with AWS Parameter Store
- ✅ Zero-maintenance system that runs forever
- ✅ Cost of ~$0.01/month to operate

## ⏱️ **Time Required**
- **First-time setup**: 90 minutes
- **If you have AWS experience**: 60 minutes
- **If you're technical**: 45 minutes

## 📋 **Prerequisites**

### **Required Accounts & Hardware:**
- [ ] Tesla Powerwall 3 installed and operational
- [ ] AWS Account with credit card on file
- [ ] Discord account and server
- [ ] GitHub account (free)
- [ ] Tesla account (same as Tesla mobile app)

### **Skills Needed:**
- Basic computer skills (copy/paste, following instructions)
- Ability to create accounts and navigate websites
- **No programming experience required**

### **What You'll Need Ready:**
- [ ] Tesla account email and password
- [ ] AWS account with billing enabled
- [ ] Discord server where you can create webhooks
- [ ] 90 minutes of uninterrupted time

## 📑 **Setup Process Overview**

The setup process has 6 main steps:

1. **[Tesla Fleet API Setup](#step-1-tesla-fleet-api-setup)** (20 minutes + 1-3 days approval)
2. **[GitHub Domain Setup](#step-2-github-domain-setup)** (10 minutes)
3. **[AWS Infrastructure Setup](#step-3-aws-infrastructure-setup)** (30 minutes)
4. **[Discord Configuration](#step-4-discord-configuration)** (5 minutes)
5. **[Token Generation](#step-5-token-generation)** (15 minutes)
6. **[Testing & Deployment](#step-6-testing--deployment)** (15 minutes)

---

## **Step 1: Tesla Fleet API Setup**

### **What This Does**
Registers your application with Tesla to get API access credentials.

### **Time Required:** 20 minutes + 1-3 days for Tesla approval

### **Detailed Instructions**
👉 **[Follow the Tesla Fleet API Setup Guide](01-tesla-fleet-api-setup.md)**

**Key Points:**
- You'll create a Tesla Developer account
- Submit an application for API access
- Wait for Tesla approval (1-3 business days)
- Get your Client ID and Client Secret

**⚠️ Important:** You cannot proceed to the final steps until Tesla approves your application. However, you can complete Steps 2-4 while waiting.

**What You'll Have After This Step:**
- ✅ Tesla Developer account
- ✅ Approved application with Client ID and Client Secret
- ✅ Partner account registered with Tesla

---

## **Step 2: GitHub Domain Setup**

### **What This Does**
Creates a free website to host the public key file required by Tesla Fleet API.

### **Time Required:** 10 minutes

### **Detailed Instructions**
👉 **[Follow the GitHub Domain Setup Guide](02-github-domain-setup.md)**

**Key Points:**
- Creates free GitHub Pages website at `https://yourusername.github.io`
- Hosts Tesla's required public key file
- No cost and no complex DNS setup required

**What You'll Have After This Step:**
- ✅ Free website at `https://yourusername.github.io`
- ✅ Public key file accessible to Tesla
- ✅ Domain ready for Tesla Fleet API registration

---

## **Step 3: AWS Infrastructure Setup**

### **What This Does**
Deploys the AWS infrastructure (Lambda functions, EventBridge schedules, Parameter Store) that powers your automation.

### **Time Required:** 30 minutes

### **Choose Your Deployment Method:**

**Option A: UI Deployment (Recommended for Beginners)**
👉 **[Follow the AWS Infrastructure UI Setup Guide](03-aws-infrastructure-setup.md)**
- Uses AWS Console web interface
- Step-by-step screenshots and instructions
- No command line required

**Option B: CloudFormation Deployment (Recommended for Advanced Users)**
👉 **[Follow the CloudFormation Deployment Guide](deployment/cloudformation/README.md)**
- Infrastructure as Code approach
- Single command deployment
- Professional, repeatable setup

**What You'll Have After This Step:**
- ✅ 2 Lambda functions (token refresh + Powerwall scheduler)
- ✅ IAM role with proper permissions
- ✅ Parameter Store for secure credential storage
- ✅ 6 EventBridge schedules for automation
- ✅ CloudWatch logging and monitoring

---

## **Step 4: Discord Configuration**

### **What This Does**
Sets up beautiful Discord notifications so you can see what your system is doing.

### **Time Required:** 5 minutes

### **Detailed Instructions**
👉 **[Follow the Discord Configuration Guide](04-discord-configuration.md)**

**Key Points:**
- Creates Discord webhook for notifications
- Sets up rich, formatted messages with live data
- Optional but highly recommended

**Example Notification:**
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

**What You'll Have After This Step:**
- ✅ Discord server with webhook configured
- ✅ Webhook URL stored in AWS Parameter Store
- ✅ Test notification working

---

## **Step 5: Token Generation**

### **What This Does**
Completes the OAuth flow to get your first access and refresh tokens from Tesla.

### **Time Required:** 15 minutes

### **Prerequisites for This Step:**
- ✅ Tesla Fleet API application **approved** (from Step 1)
- ✅ AWS infrastructure deployed (from Step 3)
- ✅ GitHub domain active (from Step 2)

### **Detailed Instructions**
👉 **[Follow the Token Generation Guide](05-token-generation.md)**

**Key Points:**
- Complete Tesla OAuth authorization flow
- Get your first access and refresh tokens
- Update AWS Parameter Store with real tokens
- Test that everything connects properly

**What You'll Have After This Step:**
- ✅ Valid Tesla access token (8 hours validity)
- ✅ Valid Tesla refresh token (3 months validity, auto-renewed)
- ✅ Tokens stored securely in AWS Parameter Store
- ✅ Successful test of Tesla API connection

---

## **Step 6: Testing & Deployment**

### **What This Does**
Tests your complete system end-to-end and deploys the production schedules.

### **Time Required:** 15 minutes

### **Detailed Instructions**
👉 **[Follow the Testing & Deployment Guide](06-testing-deployment.md)**

**Key Points:**
- Test all Lambda functions manually
- Verify Powerwall control works
- Enable production schedules
- Monitor first automated execution

**What You'll Have After This Step:**
- ✅ Fully tested and working system
- ✅ Production schedules active
- ✅ First automated Powerwall change confirmed
- ✅ Beautiful Discord notifications flowing
- ✅ Zero-maintenance automation running

---

## 🎉 **Congratulations! Your System is Live**

Once you complete all 6 steps, your Tesla Powerwall automation system will be fully operational!

### **What Happens Next:**

**Daily Automatic Operations:**
- **9:00 PM UTC**: Primary token refresh + Discord notification
- **10:00 PM UTC**: Backup token refresh + Discord notification
- **11:31 PM UTC**: Set backup reserve to 100% + Discord notification
- **12:29 AM UTC**: Set backup reserve to 0% + Discord notification
- **1:31 AM UTC**: Set backup reserve to 100% + Discord notification
- **5:29 AM UTC**: Set backup reserve to 0% + Discord notification

**Total: 6 notifications per day showing your system is working perfectly**

### **System Benefits:**
- 💰 **Optimizes electricity costs** based on your time-of-use rates
- 🔋 **Maximizes solar energy usage** during optimal periods
- 🛡️ **Maintains backup power** when you need it most
- 📱 **Keeps you informed** with beautiful notifications
- 🔄 **Runs automatically** with zero maintenance required
- 💸 **Costs ~$0.01/month** to operate

---

## 🔧 **Customization Options**

Once your system is running, you can customize it:

### **Change Schedule Times**
Update EventBridge cron expressions for your timezone:
- **US Eastern**: Add 4-5 hours to desired local time
- **US Pacific**: Add 7-8 hours to desired local time
- **Australian Eastern**: Subtract 10-11 hours from desired local time

### **Change Backup Percentages**
Modify EventBridge event payloads:
```json
{
  "backup_reserve_percent": 75,
  "schedule_name": "Custom Schedule - Set to 75%"
}
```

### **Add More Schedules**
Create additional EventBridge rules for:
- Weekend-specific schedules
- Seasonal adjustments
- Storm preparation
- Special events

### **Different Use Cases**

**Time-of-Use Optimization:**
- High backup reserve during peak rate hours
- Low backup reserve during off-peak hours
- Zero reserve during super off-peak charging

**Solar Maximization:**
- Low reserve during peak solar hours
- High reserve before/after solar production
- Weather-based adjustments (future enhancement)

**Backup Power Priority:**
- Always maintain high backup reserves
- Minimize grid dependence
- Emergency preparedness focus

---

## 📊 **Monitoring Your System**

### **Discord Notifications**
You'll receive notifications for:
- ✅ **Successful operations** (green color)
- ⚠️ **Warnings** (orange color) - temporary issues
- 🚨 **Errors** (red color) - requires attention
- 💥 **System crashes** (purple color) - rare but handled

### **Tesla Mobile App**
- Check that backup reserve changes match your schedule
- Monitor battery level and power flow
- Verify system is working as expected

### **AWS CloudWatch**
- View Lambda execution logs
- Monitor system performance
- Set up additional alerts if desired

### **Weekly Check (Optional)**
- Review Discord notifications for any patterns
- Check AWS costs (should be ~$0.01/month)
- Verify Tesla app shows expected changes

---

## 💰 **Cost Breakdown**

Your system costs approximately **$0.01 per month** to operate:

| AWS Service | Monthly Usage | Monthly Cost |
|-------------|---------------|--------------|
| Lambda Invocations | ~180 executions | $0.0000036 |
| Lambda Compute Time | ~30 seconds total | $0.0000050 |
| Parameter Store | 5 parameters | $0.000 (free tier) |
| EventBridge | 6 rules, 180 events | $0.000 (free tier) |
| CloudWatch Logs | Basic logging | $0.000 (free tier) |
| **Total** | | **~$0.01/month** |

**Annual cost: ~$0.12** 🤯

---

## 🛡️ **Security & Privacy**

Your system is designed with security in mind:

### **What's Encrypted:**
- ✅ All Tesla credentials in AWS Parameter Store (AES-256)
- ✅ Discord webhook URLs
- ✅ All API communications use HTTPS
- ✅ AWS IAM roles with minimal permissions

### **What's Never Stored:**
- ❌ No Tesla passwords
- ❌ No personal identifying information
- ❌ No location data
- ❌ No energy usage patterns beyond what Tesla already has

### **Access Control:**
- Only your AWS account can access your credentials
- Lambda functions have minimal required permissions
- No external access to your Tesla account
- You can revoke access anytime through Tesla Developer Portal

---

## 🚨 **Emergency Procedures**

### **If Something Goes Wrong:**
1. **Tesla app manual override** works immediately
2. **Check Discord** for error notifications
3. **Review [troubleshooting guide](troubleshooting.md)** for common issues
4. **Disable EventBridge rules** to stop automation temporarily
5. **Regenerate tokens** if authentication fails

### **System Recovery:**
- All problems are recoverable
- No permanent damage possible to your Powerwall
- Manual control always available through Tesla app
- Complete system recovery possible in 15 minutes

---

## 📞 **Getting Help**

If you encounter issues during setup:

### **Documentation:**
1. **Check the specific step guide** for detailed troubleshooting
2. **Review [troubleshooting guide](troubleshooting.md)** for common issues
3. **Check [GitHub Issues](../../issues)** for similar problems

### **Community Support:**
1. **[GitHub Discussions](../../discussions)** for questions and help
2. **[Create an issue](../../issues/new)** for bugs or problems
3. **Tesla and AWS community forums** for platform-specific questions

### **Self-Help Resources:**
- **AWS documentation** for AWS-specific issues
- **Tesla Developer Portal** for API-related questions
- **Discord support** for webhook issues

---

## 🔮 **What's Next?**

After your system is running:

### **Short Term:**
- Monitor system for first week to ensure reliability
- Fine-tune schedules based on your electricity rates
- Share your success with the Tesla community!

### **Future Enhancements:**
- Weather-based scheduling (storm preparation)
- Dynamic pricing integration (real-time rate optimization)
- Home Assistant integration
- Mobile app for remote control
- Multiple Powerwall support

### **Contributing Back:**
- ⭐ Star the project on GitHub
- 📝 Share your schedule configurations
- 🐛 Report any issues you find
- 🤝 Help other users with their setups
- 💡 Suggest new features or improvements

---

## 🎯 **Success Metrics**

You'll know your system is working perfectly when:

- ✅ **Discord notifications arrive on schedule** (6 per day)
- ✅ **Tesla app shows backup reserve changes** matching your schedule
- ✅ **No error notifications** received
- ✅ **AWS costs stay around $0.01/month**
- ✅ **Electricity bill optimization** visible over time

---

## 🏆 **Achievement Unlocked!**

**You've just built an enterprise-grade, automated Tesla Powerwall optimization system that:**

- 🤖 **Runs automatically** with zero maintenance
- 💰 **Saves money** on electricity bills
- 🔋 **Maximizes energy efficiency**
- 📱 **Keeps you informed** with beautiful notifications
- 🛡️ **Operates reliably** with dual redundancy
- 💸 **Costs almost nothing** to run
- 🔒 **Maintains security** with enterprise practices
- ⚡ **Works forever** once set up

**Welcome to the future of home energy automation!** 🔋⚡🏠

---

**Need help with any step? Check the individual guides linked above or visit our [troubleshooting guide](troubleshooting.md).**

**Questions? [Open a discussion](../../discussions) and the community will help!**

**Working great? ⭐ Star this repo to help others find it!**