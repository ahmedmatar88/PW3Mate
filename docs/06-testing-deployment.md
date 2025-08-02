# Testing & Schedule Deployment

Comprehensive testing of your Tesla Powerwall automation system and deployment of production schedules.

## 🎯 **What You'll Accomplish**

- Complete end-to-end system testing
- Verify all components work together
- Deploy production schedules
- Set up monitoring and maintenance
- Ensure system reliability

**Time Required:** 15 minutes testing + ongoing monitoring

---

## 📋 **Prerequisites**

- ✅ Tesla Fleet API setup complete
- ✅ AWS infrastructure deployed
- ✅ Discord notifications configured
- ✅ OAuth tokens generated and working
- ✅ Initial Lambda tests successful

---

## 🧪 **Step 1: Component Testing**

### 1.1 Test Token Refresh System

**Test Primary Token Refresh:**
1. **Go to `PW3Mate-Token-Refresh` Lambda**
2. **Click "Test" → "Invoke"**
3. **Expected results**:
   - ✅ Status Code: 200
   - ✅ Response: "Token refresh completed"
   - ✅ Discord notification: Green success message
   - ✅ New tokens stored in Parameter Store

**Verify new tokens:**
1. **Go to Parameter Store**
2. **Check `/tesla/powerwall/last_token_refresh`**
3. **Should show current timestamp**

### 1.2 Test Powerwall Control

**Test Backup Reserve Changes:**
1. **Go to `PW3Mate-Powerwall-Scheduler` Lambda**
2. **Create test with different percentages**:

**Test 1 - Set to 80%:**
```json
{
  "backup_reserve_percent": 80,
  "schedule_name": "Test 1 - Set to 80%"
}
```

**Test 2 - Set to 30%:**
```json
{
  "backup_reserve_percent": 30,
  "schedule_name": "Test 2 - Set to 30%"
}
```

**Test 3 - Set to 50% (Reset):**
```json
{
  "backup_reserve_percent": 50,
  "schedule_name": "Test 3 - Reset to 50%"
}
```

**For each test, verify:**
- ✅ Lambda execution successful
- ✅ Tesla app shows backup reserve change
- ✅ Discord notification with live data
- ✅ No errors in CloudWatch logs

### 1.3 Test Error Handling

**Test with invalid percentage:**
```json
{
  "backup_reserve_percent": 150,
  "schedule_name": "Error Test - Invalid Percentage"
}
```

**Expected results:**
- ❌ Lambda should handle gracefully
- 🚨 Error notification in Discord
- 📝 Detailed error in CloudWatch logs

---

## ⏰ **Step 2: Schedule Verification**

### 2.1 Review EventBridge Rules

**Go to [EventBridge Console](https://console.aws.amazon.com/events/) → Rules**

**Verify these rules exist and are enabled:**

**Token Refresh Schedules:**
- ✅ `PW3Mate-Token-Refresh-9PM` - `cron(0 21 * * ? *)`
- ✅ `PW3Mate-Token-Refresh-10PM` - `cron(0 22 * * ? *)`

**Powerwall Schedules (adjust for your timezone):**
- ✅ `PW3Mate-Powerwall-2331-100percent` - `cron(31 23 * * ? *)`
- ✅ `PW3Mate-Powerwall-0029-0percent` - `cron(29 0 * * ? *)`
- ✅ `PW3Mate-Powerwall-0131-100percent` - `cron(31 1 * * ? *)`
- ✅ `PW3Mate-Powerwall-0529-0percent` - `cron(29 5 * * ? *)`

### 2.2 Verify Rule Configuration

**For each rule, check:**
1. **Click on rule name**
2. **Verify cron expression** matches your desired schedule
3. **Check target** points to correct Lambda function
4. **Verify input JSON** has correct backup percentage
5. **Ensure rule is enabled**

**Example rule details:**
```
Name: PW3Mate-Powerwall-2331-100percent
Schedule: cron(31 23 * * ? *)
Target: PW3Mate-Powerwall-Scheduler
Input: {"backup_reserve_percent": 100, "schedule_name": "11:31 PM - Set to 100%"}
State: Enabled
```

### 2.3 Timezone Verification

**Convert your desired local times to UTC:**

**Example for US Eastern Time:**
- Local 11:31 PM EST = 4:31 AM UTC = `cron(31 4 * * ? *)`
- Local 12:29 AM EST = 5:29 AM UTC = `cron(29 5 * * ? *)`

**Example for UK Time:**
- Local 11:31 PM GMT = 11:31 PM UTC = `cron(31 23 * * ? *)`
- Local 11:31 PM BST = 10:31 PM UTC = `cron(31 22 * * ? *)`

**Use [Cron Calculator](https://crontab.cronhub.io/) to verify your expressions.**

---

## 📊 **Step 3: Monitoring Setup**

### 3.1 CloudWatch Dashboards

**Create monitoring dashboard:**
1. **Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)**
2. **Click "Dashboards" → "Create dashboard"**
3. **Dashboard name**: `PW3Mate-Monitoring`

**Add widgets:**

**Lambda Invocations:**
- Widget type: Number
- Metric: `AWS/Lambda` → `Invocations`
- Functions: Both PW3Mate functions
- Period: 1 day

**Lambda Errors:**
- Widget type: Number
- Metric: `AWS/Lambda` → `Errors`
- Functions: Both PW3Mate functions
- Period: 1 day

**Lambda Duration:**
- Widget type: Line graph
- Metric: `AWS/Lambda` → `Duration`
- Functions: Both PW3Mate functions
- Period: 5 minutes

### 3.2 CloudWatch Alarms

**Create error alarm:**
1. **CloudWatch → Alarms → Create alarm**
2. **Metric**: `AWS/Lambda` → `Errors`
3. **Function**: `PW3Mate-Powerwall-Scheduler`
4. **Condition**: Greater than 0
5. **Period**: 5 minutes
6. **Action**: Send SNS notification (optional)

### 3.3 Log Monitoring

**Check log groups:**
- `/aws/lambda/PW3Mate-Token-Refresh`
- `/aws/lambda/PW3Mate-Powerwall-Scheduler`

**Look for:**
- ✅ Successful executions
- 🚨 Error messages
- ⚡ Performance metrics
- 🔍 Debug information

---

## 🌙 **Step 4: First Night Testing**

### 4.1 Pre-Deployment Checklist

**Before your first automated night:**
- [ ] All Lambda tests successful
- [ ] Discord notifications working
- [ ] Tesla app shows manual test changes
- [ ] EventBridge rules enabled
- [ ] Cron expressions correct for timezone
- [ ] Backup reserve percentages appropriate

### 4.2 First Night Monitoring

**What to expect:**

**9:00 PM UTC (or your equivalent):**
- 🔄 Token refresh notification in Discord
- 📝 Success message with next refresh time

**10:00 PM UTC (backup refresh):**
- 🛡️ Backup token refresh notification
- ✅ "All systems operational" message

**11:31 PM UTC (first schedule):**
- 🔋 Powerwall backup reserve changes to 100%
- 📊 Discord notification with live status
- 📱 Tesla app reflects change

**12:29 AM UTC (second schedule):**
- 🔋 Powerwall backup reserve changes to 0%
- 📊 Updated Discord notification

### 4.3 Monitoring First Night

**Stay available for:**
- First 2 hours after deployment
- Monitor Discord for notifications
- Check Tesla app for changes
- Review CloudWatch logs for errors

**If issues occur:**
- 🚨 Check Discord for error notifications
- 📝 Review CloudWatch logs
- 📱 Verify Tesla app connectivity
- 🔧 Use troubleshooting guide

---

## 🎛️ **Step 5: Production Deployment**

### 5.1 Enable All Schedules

**Ensure all rules are enabled:**
1. **Go to EventBridge → Rules**
2. **For each PW3Mate rule**:
   - Click rule name
   - Verify "State: Enabled"
   - If disabled, click "Enable"

### 5.2 Production Schedule Example

**Default schedule (adjust times for your timezone):**

```
09:00 PM UTC - Daily Token Refresh
10:00 PM UTC - Backup Token Refresh  
11:31 PM UTC - Set Backup Reserve to 100%
12:29 AM UTC - Set Backup Reserve to 0%
01:31 AM UTC - Set Backup Reserve to 100%
05:29 AM UTC - Set Backup Reserve to 0%
```

**This schedule optimizes for:**
- ✅ Cheap overnight charging (0% reserve)
- ✅ Peak hour backup power (100% reserve)
- ✅ Reliable token refresh (dual system)

### 5.3 Customize for Your Needs

**Time-of-Use Optimization:**
- Set 100% before peak hours start
- Set 0% during super off-peak hours
- Maintain moderate reserve during shoulder periods

**Seasonal Adjustments:**
- Higher reserves in winter (heating backup)
- Lower reserves in summer (solar abundance)
- Storm season preparation (higher reserves)

**Weekend Variations:**
- Different schedule for weekend usage patterns
- Separate rules for weekdays vs weekends

---

## 📈 **Step 6: Performance Optimization**

### 6.1 Cost Monitoring

**Set up billing alerts:**
1. **AWS Billing → Budgets → Create budget**
2. **Budget type**: Cost budget
3. **Amount**: $2.00/month (buffer above expected $0.01)
4. **Alert**: 80% of budget used

**Expected monthly costs:**
```
Lambda Invocations: ~180/month = $0.0000036
Lambda Compute: ~30 seconds total = $0.0000050
Parameter Store: Free tier
EventBridge: Free tier
CloudWatch: Free tier (basic)
Total: ~$0.01/month
```

### 6.2 Performance Metrics

**Monitor these key metrics:**
- **Success Rate**: Should be >99%
- **Execution Duration**: Should be <10 seconds
- **Token Refresh Success**: Should be 100%
- **Schedule Accuracy**: Should be ±1 minute

### 6.3 Optimization Opportunities

**Lambda Optimization:**
- Increase memory if execution is slow
- Add retry logic for network issues
- Implement exponential backoff

**Schedule Optimization:**
- Analyze electricity usage patterns
- Adjust percentages based on seasonal needs
- Add weather-based intelligence (future)

---

## 🔧 **Step 7: Maintenance and Monitoring**

### 7.1 Weekly Checks

**Every week, verify:**
- [ ] Discord notifications still working
- [ ] Tesla app shows expected changes
- [ ] No error notifications received
- [ ] CloudWatch logs show success

### 7.2 Monthly Maintenance

**Monthly tasks:**
- [ ] Review AWS costs (should be ~$0.01)
- [ ] Check token refresh success rate
- [ ] Verify schedule accuracy
- [ ] Update documentation if needed

### 7.3 Quarterly Reviews

**Quarterly optimization:**
- [ ] Analyze energy usage patterns
- [ ] Adjust schedules for seasonal changes
- [ ] Review security and access
- [ ] Update dependencies if needed

---

## 🚨 **Emergency Procedures**

### 7.1 System Failure Response

**If automation stops working:**
1. **Check Discord** for error notifications
2. **Manually adjust** Powerwall via Tesla app
3. **Review CloudWatch logs** for errors
4. **Check EventBridge rules** are enabled
5. **Test Lambda functions** manually

### 7.2 Token Expiration Emergency

**If tokens expire unexpectedly:**
1. **Generate new tokens** via OAuth flow
2. **Update Parameter Store** immediately
3. **Test token refresh** Lambda manually
4. **Resume normal operations**

### 7.3 Powerwall Emergency Override

**For emergencies (power outages, etc.):**
1. **Tesla app manual override** works immediately
2. **Automation will resume** at next scheduled time
3. **No permanent changes** to automation system

---

## ✅ **Success Metrics**

### 7.1 System Health Indicators

**Healthy system shows:**
- ✅ Regular Discord notifications (6/day)
- ✅ Tesla app changes match schedule
- ✅ No error messages or alerts
- ✅ Consistent execution times
- ✅ Stable AWS costs (~$0.01/month)

### 7.2 Energy Optimization Metrics

**Track improvements:**
- 📊 Electricity bill changes
- ⚡ Peak demand reduction
- ☀️ Solar energy utilization
- 🔋 Battery cycling efficiency
- 💰 Cost savings over time

---

## 🎉 **Congratulations!**

### Your Tesla Powerwall automation system is now fully operational!

**What you've achieved:**
- ✅ **Fully automated** Powerwall backup reserve scheduling
- ✅ **Enterprise-grade reliability** with dual token refresh
- ✅ **Beautiful notifications** for all system events
- ✅ **Cost-effective operation** at ~$0.01/month
- ✅ **Zero maintenance** required for ongoing operation
- ✅ **Professional monitoring** and error handling

**Your system will now:**
- 🔄 Automatically refresh tokens twice daily
- 🔋 Adjust backup reserve according to your schedule
- 📱 Send notifications for all changes and status
- 🛡️ Handle errors gracefully with backup systems
- 💰 Optimize your electricity costs continuously

---

## 🔮 **What's Next?**

### **Immediate Next Steps:**
1. **Monitor first week** of operation closely
2. **Fine-tune schedules** based on usage patterns
3. **Share your success** with the Tesla community
4. **Consider contributing** improvements back to the project

### **Future Enhancements:**
- **Weather integration** for storm preparation
- **Dynamic pricing** integration for real-time optimization
- **Multiple Powerwall** support
- **Home Assistant** integration
- **Mobile app** for remote control

### **Community Contributions:**
- ⭐ **Star the project** on GitHub
- 📝 **Share your configuration** examples
- 🐛 **Report issues** and improvements
- 🤝 **Help other users** with their setups

---

## 📞 **Support Resources**

### **Documentation:**
- 📖 [Complete Setup Guide](../setup-guide.md)
- 🔧 [Troubleshooting Guide](../troubleshooting.md)
- 💡 [Advanced Configuration](../advanced-configuration.md)

### **Community:**
- 💬 [GitHub Discussions](../../discussions)
- 🐛 [Issue Tracker](../../issues)
- 📧 [Email Support](mailto:support@example.com)

### **Emergency Contacts:**
- 🚨 Tesla app manual override (immediate)
- ☁️ AWS support (billing/technical issues)
- 💬 Discord webhooks (notification issues)

---

**🎯 Your Tesla Powerwall is now optimizing itself 24/7!**

**Enjoy your automated, cost-optimized, reliable energy management system! ⚡🔋🏠**

---

## 📋 **Final Checklist**

**System Deployment Complete:**
- [ ] All Lambda functions tested and working
- [ ] EventBridge schedules enabled and correct
- [ ] Discord notifications functioning properly
- [ ] Tesla app shows automated changes
- [ ] CloudWatch monitoring configured
- [ ] First night monitoring completed successfully
- [ ] Documentation bookmarked for future reference
- [ ] Emergency procedures understood

**🏆 PW3Mate Tesla Powerwall Automation: DEPLOYED AND OPERATIONAL! 🏆**