# Tesla Powerwall Automation 🔋⚡

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)

Fully automated Tesla Powerwall backup reserve scheduling using AWS Lambda and Tesla's official Fleet API. Set your Powerwall backup reserve on a custom schedule with beautiful Discord notifications and enterprise-grade reliability.

## 🎯 **What This Does**

Automatically adjusts your Tesla Powerwall backup reserve percentage on a schedule you define:

For Example:

- **11:31 PM** → Set backup reserve to **100%**
- **12:29 AM** → Set backup reserve to **0%** 
- **1:31 AM** → Set backup reserve to **100%**
- **5:29 AM** → Set backup reserve to **0%**

Perfect for time-of-use electricity billing or optimising solar energy usage!

## ✨ **Features**

- 🔄 **Fully Automated** - Zero maintenance after setup
- 🛡️ **Dual Redundancy** - Two daily token refreshes for maximum reliability  
- 📱 **Beautiful Notifications** - Rich Discord embeds with live Powerwall data
- 🔐 **Enterprise Security** - All credentials encrypted in AWS Parameter Store
- 💰 **Cost Effective** - Runs for approximately $0.01/month
- ⚙️ **Easy Customization** - Modify schedules without code changes
- 🔧 **Error Recovery** - Automatic backup systems and detailed error reporting
- 📊 **Live Status** - Real-time battery level, solar production, and power flow data

## 📱 **Discord Notifications**

Get beautiful, informative notifications for every operation

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌───────────────────┐
│   EventBridge   │───▶│  Lambda Function │───▶│ Tesla Fleet API   │
│   (Scheduler)   │    │   (Token Refresh │    │                   │
└─────────────────┘    │   & Powerwall)   │    └───────────────────┘
                       └──────────────────┘                        
                                │                                   
                                ▼                                   
                       ┌──────────────────┐    ┌───────────────────┐
                       │ Parameter Store  │    │ Discord Webhook   │
                       │  (Credentials)   │    │ (Notifications)   │
                       └──────────────────┘    └───────────────────┘
```


## 🚀 **Quick Start**

### Prerequisites
- Tesla Powerwall 3
- AWS Account with Lambda access
- Discord server (for notifications)
- Tesla Fleet API developer account

### 1. Tesla Fleet API Setup
1. Register at [Tesla Developer Portal](https://developer.tesla.com/)
2. Create your application and get client credentials
3. Complete the Fleet API registration process
4. Generate initial OAuth tokens

### 2. AWS Deployment
1. Deploy the Lambda functions using our automated scripts
2. Configure AWS Parameter Store with your Tesla credentials
3. Set up EventBridge schedules for automation
4. Configure Discord webhook for notifications

### 3. Test & Enjoy
Run the test suite to verify everything works, then sit back and let your Powerwall optimize itself!

**👉 [Complete Setup Guide](docs/setup-guide.md)**


## 🛠️ **Customization**

### Change Backup Percentages
Update EventBridge event payloads:
```json
{
  "backup_reserve_percent": 75,
  "schedule_name": "11:31 PM - Set to 75%"
}
```

### Add More Schedules
Create additional EventBridge rules with different times and percentages.

## 📁 **Project Structure**

```
tesla-powerwall-scheduler/
├── src/lambda/                    # Lambda function source code
├── docs/                          # Comprehensive documentation  
├── deployment/                    # AWS deployment templates
├── scripts/                       # Automation and utility scripts
├── examples/                      # Configuration examples
└── tests/                         # Test suite
```

## 🔧 **Development**

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test Tesla API connection
python src/local/test_api.py

# Generate initial tokens
python src/local/generate_tokens.py
```

### Deployment
```bash
# Automated deployment
./scripts/deploy.sh

# Manual deployment
aws lambda create-function ...
```

## 🐛 **Troubleshooting**

Common issues and solutions:

- **Token Expired**: System automatically refreshes tokens daily
- **API Rate Limits**: Built-in retry logic and exponential backoff
- **Network Issues**: Dual refresh system provides redundancy
- **Missing Notifications**: Check Discord webhook configuration

**👉 [Full Troubleshooting Guide](docs/troubleshooting.md)**

## 💰 **Cost Breakdown**

| Service | Monthly Cost |
|---------|-------------|
| AWS Lambda (executions) | ~$0.006 |
| AWS Parameter Store | $0.000 |
| AWS EventBridge | $0.000 |
| **Total** | **~$0.01/month** |

*Based on standard schedule (6 executions/day)*

## 🤝 **Contributing**

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) and:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ **Disclaimer**

This project is not affiliated with Tesla, Inc. Use at your own risk. Always monitor your energy system and ensure any automation aligns with your local utility requirements and safety standards.

## 🙏 **Acknowledgments**

- Tesla for providing the Fleet API
- AWS for reliable serverless infrastructure
- Discord for excellent webhook notifications
- The open-source community for inspiration and tools

## 📞 **Support**

- 📖 Check the [documentation](docs/)
- 🐛 Report bugs via [GitHub Issues](../../issues)
- 💬 Join discussions in [GitHub Discussions](../../discussions)
- ⭐ Star this repo if it helped you!

---

**Made with ⚡ for Tesla Powerwall owners who love automation**
