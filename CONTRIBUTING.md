# Contributing to Gmail Order Processor (Local)

Thank you for your interest in contributing to this project! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- A Gmail account with App Password capability
- Access to an inFlow inventory system (for testing)

### Development Setup
1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/gmail-order-processor-local.git
   cd gmail-order-processor-local
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set up your environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

## 🔧 Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose
- Maximum line length: 120 characters

### Code Structure
- `local_main.py` - Main application logic and monitoring loop
- `local_gmail_service.py` - Gmail IMAP operations
- `local_storage.py` - File-based storage for tracking
- `local_config.py` - Configuration management
- `order_processor.py` - Email parsing and order extraction
- `inflow_api.py` - inFlow API client
- `run_local.py` - Startup script with validation

### Testing
- Add tests for new functionality in `tests/` directory
- Run existing tests before submitting:
  ```bash
  python -m pytest tests/
  ```
- Test with real Gmail/inFlow connections when possible
- Include both positive and negative test cases

### Logging
- Use the existing logger instances
- Log at appropriate levels:
  - `DEBUG` - Detailed debugging information
  - `INFO` - General operation information
  - `WARNING` - Potential issues that don't stop operation
  - `ERROR` - Errors that prevent operation
- Include context in log messages (execution IDs, email IDs, etc.)

## 📝 Types of Contributions

### Bug Reports
When reporting bugs, please include:
- Python version and operating system
- Complete error message and traceback
- Steps to reproduce the issue
- Expected vs actual behavior
- Log file contents (with sensitive data removed)

### Feature Requests
For new features, please:
- Describe the use case and problem being solved
- Explain why this would be valuable to other users
- Consider backward compatibility
- Suggest implementation approach if possible

### Code Contributions
1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clear, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test thoroughly:**
   - Run all existing tests
   - Test with real Gmail/inFlow connections
   - Test error conditions and edge cases

4. **Commit with clear messages:**
   ```bash
   git commit -m "Add feature: brief description
   
   Longer explanation of what changed and why.
   Include any breaking changes or migration notes."
   ```

5. **Push and create Pull Request:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Documentation
- Update README.md for user-facing changes
- Update SETUP.md for configuration changes
- Add or update docstrings for code changes
- Include examples for new features

## 🔍 Pull Request Process

1. **Before submitting:**
   - Ensure your branch is up to date with main
   - Run tests and verify they pass
   - Check that the application starts and processes emails
   - Review your changes for any sensitive data

2. **Pull request description:**
   - Clearly describe what the PR does
   - Reference any related issues
   - Include screenshots for UI changes
   - List any breaking changes
   - Note any new dependencies

3. **Review process:**
   - Maintainers will review your PR
   - Address any feedback or requested changes
   - Once approved, your PR will be merged

## 🎯 Priority Areas

We're especially interested in contributions for:

### High Priority
- **Error handling improvements** - Better recovery from network issues
- **Performance optimizations** - Faster email processing
- **Security enhancements** - Better credential handling
- **Documentation improvements** - Clearer setup instructions

### Medium Priority
- **Database storage option** - SQLite/PostgreSQL instead of JSON files
- **Web dashboard** - Browser-based monitoring interface
- **Docker support** - Containerization for easier deployment
- **Multi-threading** - Parallel email processing

### Nice to Have
- **Email template customization** - Support for different email formats
- **Webhook notifications** - Real-time alerts for new orders
- **Monitoring integrations** - Prometheus/Grafana support
- **Cloud deployment guides** - AWS/Azure/GCP deployment

## 🐛 Debugging Tips

### Common Issues
1. **Gmail connection failures:**
   - Verify App Password is correct
   - Check 2FA is enabled on Gmail account
   - Test IMAP connection manually

2. **inFlow API errors:**
   - Verify API key and company ID
   - Check customer/product names match exactly
   - Monitor rate limiting

3. **File permission errors:**
   - Ensure write access to local_data directory
   - Check file locking on shared filesystems

### Development Debugging
- Set `LOG_LEVEL=DEBUG` for verbose logging
- Use `python -u` for unbuffered output
- Add temporary print statements for tracing
- Test individual components with their test functions

## 📋 Code Review Checklist

Before submitting, ensure:
- [ ] Code follows Python PEP 8 style guidelines
- [ ] All functions have docstrings
- [ ] New features include tests
- [ ] No sensitive data (passwords, API keys) in code
- [ ] Error handling is appropriate
- [ ] Logging provides useful information
- [ ] Documentation is updated
- [ ] Backward compatibility is maintained
- [ ] Performance impact is considered

## 🤝 Community Guidelines

- Be respectful and constructive in discussions
- Help others with setup and troubleshooting
- Share your use cases and feature ideas
- Report security issues privately to maintainers
- Follow the project's code of conduct

## 📞 Getting Help

- **Setup Issues:** Check SETUP.md and QUICK_START.md
- **Bug Reports:** Create a GitHub issue with details
- **Feature Discussions:** Start a GitHub discussion
- **Questions:** Create a GitHub issue with the "question" label

Thank you for contributing to Gmail Order Processor! 🎉