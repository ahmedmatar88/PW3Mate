# Contributing to PW3Mate

Thank you for your interest in contributing to PW3Mate! This project helps Tesla Powerwall owners automate their backup reserve scheduling, and we welcome contributions from the community.

## 🎯 **Project Goals**

PW3Mate aims to:
- Provide reliable, automated Tesla Powerwall backup reserve scheduling
- Maintain enterprise-grade security and reliability
- Offer clear documentation for users of all technical levels
- Support diverse use cases (time-of-use billing, solar optimization, etc.)
- Keep operational costs minimal (~$0.01/month)

## 🤝 **Ways to Contribute**

### 📝 **Documentation**
- Improve setup guides and troubleshooting docs
- Add examples for different use cases or regions
- Translate documentation to other languages
- Create video tutorials or walkthroughs

### 🐛 **Bug Reports**
- Report issues with setup, configuration, or operation
- Provide detailed reproduction steps and logs
- Suggest fixes or workarounds

### ✨ **Feature Requests**
- Propose new scheduling algorithms
- Suggest additional notification methods
- Request integration with other smart home systems

### 💻 **Code Contributions**
- Fix bugs in Lambda functions
- Add new notification providers (SMS, email, etc.)
- Improve error handling and resilience
- Add monitoring and alerting features

### 🧪 **Testing**
- Write unit or integration tests
- Test on different AWS regions
- Validate with different Powerwall configurations

## 🚀 **Getting Started**

### 1. **Set Up Development Environment**

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/PW3Mate.git
cd PW3Mate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### 2. **Understand the Architecture**

```
Tesla Fleet API ←→ AWS Lambda ←→ Parameter Store
       ↑                 ↓
   Powerwall         Discord/Notifications
```

**Key Components:**
- `src/lambda/token_refresh/` - Daily token refresh logic
- `src/lambda/powerwall_scheduler/` - Powerwall backup reserve control
- `docs/` - User documentation and guides
- `examples/` - Configuration templates and samples

### 3. **Local Testing**

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests (requires AWS credentials)
pytest tests/integration/

# Test specific function
python -m pytest tests/unit/test_token_refresh.py -v

# Run with coverage
pytest --cov=src tests/
```

## 📋 **Contribution Guidelines**

### **Code Style**

We use Python best practices:

```bash
# Format code with Black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

**Key principles:**
- ✅ Clear, descriptive variable and function names
- ✅ Comprehensive error handling and logging
- ✅ Type hints for function parameters and returns
- ✅ Docstrings for all public functions
- ✅ No hardcoded credentials or secrets

### **Security Requirements**

🔒 **Critical**: Never commit sensitive data!

**Security checklist:**
- ❌ Never commit Tesla credentials, tokens, or private keys
- ❌ Never hardcode AWS credentials or ARNs
- ❌ Never commit Discord webhook URLs or notification credentials
- ✅ Use Parameter Store references in code
- ✅ Store secrets in `.env` files (which are gitignored)
- ✅ Sanitize logs to remove sensitive information
- ✅ Use placeholder values in documentation examples

### **Documentation Standards**

- **Clear headings** with emoji for visual hierarchy
- **Step-by-step instructions** with screenshots where helpful
- **Code examples** with proper syntax highlighting
- **Prerequisites** clearly listed at the start
- **Troubleshooting sections** for common issues
- **Cross-references** to related documentation

### **Testing Standards**

**All code changes should include:**
- ✅ Unit tests for new functions
- ✅ Integration tests for AWS interactions
- ✅ Mock tests for Tesla API calls
- ✅ Error condition testing
- ✅ Documentation updates

**Test coverage goals:**
- Lambda functions: >90% coverage
- Critical paths: 100% coverage
- Error handling: Comprehensive coverage

## 🔄 **Development Workflow**

### **1. Create Feature Branch**

```bash
# Create branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b bugfix/issue-description

# For documentation
git checkout -b docs/improvement-description
```

### **2. Make Changes**

- Write code following our style guidelines
- Add comprehensive tests
- Update documentation as needed
- Test locally before committing

### **3. Commit Guidelines**

Use conventional commit format:

```bash
# Feature additions
git commit -m "feat: add SMS notification support"

# Bug fixes
git commit -m "fix: handle token refresh timeout gracefully"

# Documentation
git commit -m "docs: improve AWS setup guide with screenshots"

# Tests
git commit -m "test: add integration tests for Powerwall scheduler"

# Refactoring
git commit -m "refactor: simplify parameter store manager"
```

### **4. Submit Pull Request**

1. **Push your branch** to your fork
2. **Create pull request** against `main` branch
3. **Provide clear description** of changes
4. **Reference any related issues**
5. **Ensure all CI checks pass**

## 🧪 **Testing Your Contributions**

### **Unit Tests**

```bash
# Test specific component
pytest tests/unit/test_token_refresh.py::test_refresh_success -v

# Test with coverage
pytest --cov=src/lambda/token_refresh tests/unit/test_token_refresh.py
```

### **Integration Tests**

```bash
# Set up test environment
export AWS_PROFILE=your-test-profile
export TESLA_CLIENT_ID=test-client-id

# Run integration tests
pytest tests/integration/ -v
```

### **Local Lambda Testing**

```bash
# Test token refresh locally
cd src/lambda/token_refresh
python lambda_function.py

# Test with mock event
python -c "
import lambda_function
result = lambda_function.lambda_handler({}, None)
print(result)
"
```

## 📚 **Documentation Contributions**

### **Setup Guides**

When improving setup documentation:
- ✅ Test instructions on fresh AWS account
- ✅ Include screenshots for complex UI steps  
- ✅ Provide troubleshooting for common errors
- ✅ Update time estimates based on actual experience

### **Examples and Templates**

- Create realistic, working examples
- Include comments explaining configuration choices
- Provide variations for different use cases
- Test all examples before submitting

### **API Documentation**

- Document all function parameters and return values
- Include example usage with expected outputs
- Explain error conditions and handling
- Keep documentation in sync with code changes

## 🐛 **Reporting Issues**

### **Bug Reports**

Please include:

1. **Environment details**:
   - AWS region
   - Python version
   - Powerwall model
   - Tesla app version

2. **Steps to reproduce**:
   - Exact sequence of actions
   - Configuration settings used
   - Expected vs actual behavior

3. **Logs and errors**:
   - CloudWatch logs (sanitized)
   - Error messages
   - Screenshots of issues

4. **Impact assessment**:
   - Frequency of occurrence
   - Workarounds (if any)
   - Business impact

### **Feature Requests**

Please provide:

1. **Use case description**:
   - Problem you're trying to solve
   - Current workarounds
   - User stories

2. **Proposed solution**:
   - High-level approach
   - Alternative solutions considered
   - Implementation complexity estimate

3. **Acceptance criteria**:
   - Success metrics
   - Edge cases to consider
   - Backward compatibility requirements

## 🏷️ **Issue Labels**

We use these labels to categorize issues:

- `bug` - Something isn't working correctly
- `enhancement` - New feature or improvement
- `documentation` - Documentation improvements
- `good first issue` - Suitable for newcomers
- `help wanted` - Extra attention needed
- `priority: high` - Critical issues
- `priority: low` - Nice to have improvements
- `aws` - AWS-related issues
- `tesla-api` - Tesla Fleet API issues
- `security` - Security-related concerns

## 💬 **Communication**

### **Getting Help**

- 📖 Check existing documentation first
- 🔍 Search existing issues and discussions
- 💬 Create GitHub Discussion for questions
- 🐛 Create GitHub Issue for bugs
- ✨ Create GitHub Issue for feature requests

### **Community Guidelines**

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers get started
- Share knowledge and experiences
- Keep discussions on-topic and professional

## 🎉 **Recognition**

Contributors will be recognized:

- 📜 Listed in project README
- 🏆 Special mentions for significant contributions
- 📢 Highlighted in release notes
- 🌟 GitHub contributor stats
- 💌 Personal thank you from maintainers

## 📄 **License**

By contributing to PW3Mate, you agree that your contributions will be licensed under the same MIT License that covers the project.

## 🔗 **Resources**

### **Tesla Fleet API**
- [Official Documentation](https://developer.tesla.com/docs/fleet-api)
- [API Reference](https://developer.tesla.com/docs/fleet-api/reference)

### **AWS Documentation**
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [EventBridge User Guide](https://docs.aws.amazon.com/eventbridge/latest/userguide/)
- [Parameter Store Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)

### **Development Tools**
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [mypy Type Checker](https://mypy.readthedocs.io/)

## 🚀 **What's Next?**

Ready to contribute? Here are some good starting points:

### **Good First Issues**
- Improve error messages in Lambda functions
- Add timezone conversion examples
- Create CloudFormation templates
- Write additional unit tests
- Improve documentation clarity

### **Advanced Contributions**
- Add new notification providers (Pushover, SMS, etc.)
- Implement cost optimization algorithms
- Create monitoring dashboards
- Add multi-Powerwall support
- Build GitHub Actions for CI/CD

### **Documentation Priorities**
- Video setup tutorials
- Region-specific setup guides
- Advanced configuration examples
- Troubleshooting flowcharts
- API reference documentation

---

**Thank you for helping make PW3Mate better for the Tesla Powerwall community! 🔋⚡**

Have questions about contributing? Start a [GitHub Discussion](../../discussions) and we'll help you get started!