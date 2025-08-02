# PW3Mate - Tesla Powerwall 3 Automation 🔋⚡

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)

Fully automated Tesla Powerwall backup reserve scheduling using AWS Lambda and Tesla's official Fleet API. Set your Powerwall backup reserve on a custom schedule with beautiful Discord notifications and enterprise-grade reliability.

## 🎯 **What This Does**

Automatically adjusts your Tesla Powerwall backup reserve percentage on a schedule you define:

**Example Schedule:**
- **11:31 PM** → Set backup reserve to **100%**
- **12:29 AM** → Set backup reserve to **0%** 
- **1:31 AM** → Set backup reserve to **100%**
- **5:29 AM** → Set backup reserve to **0%**

Perfect for time-of-use electricity billing or optimizing solar energy usage!

## ✨ **Features**

- 🔄 **Fully Automated** - Zero maintenance after setup
- 🛡️ **Dual Redundancy** - Two daily token refreshes for maximum reliability  
- 📱 **Beautiful Notifications** - Rich Discord embeds with live Powerwall data
- 🔐 **Enterprise Security** - All credentials encrypted in AWS Parameter Store
- 💰 **Cost Effective** - Runs for approximately $0.01/month
- ⚙️ **Easy Customization** - Modify schedules without code changes
- 🔧 **Error Recovery** - Automatic backup systems and detailed error reporting
- 📊 **Live Status** - Real-time battery level, solar production, and power flow data


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
- GitHub account (for Tesla Fleet API domain requirement)

### Setup Process
1. **[Tesla Fleet API Setup](docs/01-tesla-fleet-api-setup.md)** (20 minutes)
2. **[GitHub Domain Setup](docs/02-github-domain-setup.md)** (10 minutes)
3. **[AWS Infrastructure Setup](docs/03-aws-infrastructure-setup.md)** (30 minutes)  
4. **[Discord Configuration](docs/04-discord-configuration.md)** (5 minutes)
5. **[Token Generation](docs/05-token-generation.md)** (15 minutes)
6. **[Testing & Deployment](docs/06-testing-deployment.md)** (15 minutes)

**👉 [Start with the Complete Setup Guide](docs/setup-guide.md)**

## 💰 **Cost Breakdown**

| Service | Monthly Cost |
|---------|-------------|
| AWS Lambda (executions) | ~$0.006 |
| AWS Parameter Store | $0.000 |
| AWS EventBridge | $0.000 |
| GitHub Pages (domain) | $0.000 |
| **Total** | **~$0.01/month** |

*Based on standard schedule (6 executions/day)*

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

### Different Time Zones
All examples use UTC. Convert your local time:
- **US Eastern**: Add 4-5 hours to local time
- **US Pacific**: Add 7-8 hours to local time  
- **Australian Eastern**: Subtract 10-11 hours from local time

## 📁 **Project Structure**

```
PW3Mate/
├── src/
│   └── lambda/
│       ├── token_refresh/
│       │   └── lambda_function.py     # Daily token refresh
│       └── powerwall_scheduler/
│           └── lambda_function.py     # Powerwall scheduling
├── docs/
│   ├── setup-guide.md                 # Complete step-by-step guide
│   ├── troubleshooting.md            # Common issues & solutions
│   ├── 01-tesla-fleet-api-setup.md   # Tesla API registration
│   ├── 02-github-domain-setup.md     # Free domain setup
│   ├── 03-aws-infrastructure-setup.md # AWS deployment (UI)
│   ├── 04-discord-configuration.md   # Discord webhook setup
│   ├── 05-token-generation.md        # OAuth token generation
│   └── 06-testing-deployment.md      # Testing & schedule deployment
└── tests/
    ├── test_token_refresh.py         # Unit tests
    └── test_powerwall_scheduler.py   # Integration tests
```

## 🔧 **Development**

### Local Testing
```bash
# Clone repository
git clone https://github.com/yourusername/PW3Mate.git
cd PW3Mate

# Install dependencies
pip install -r requirements.txt

# Test Tesla API connection (after setup)
python tests/test_token_refresh.py
```

## 🐛 **Troubleshooting**

Common issues and solutions:

- **Token Expired**: System automatically refreshes tokens daily
- **API Rate Limits**: Built-in retry logic and exponential backoff
- **Network Issues**: Dual refresh system provides redundancy
- **Missing Notifications**: Check Discord webhook configuration

**👉 [Full Troubleshooting Guide](docs/troubleshooting.md)**

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

## 🚀 **What's Next?**

After setup, your Powerwall will:
- ✅ Automatically optimize backup reserve 4 times daily
- ✅ Send beautiful Discord notifications for all changes
- ✅ Run reliably with dual token refresh system
- ✅ Cost less than $0.01/month to operate
- ✅ Require zero maintenance

**Ready to automate your Tesla Powerwall?** Follow the [setup guide](docs/setup-guide.md) to get started!

---

**Made with ⚡ for Tesla Powerwall owners who love automation**