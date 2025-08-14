# Changelog

All notable changes to the Gmail Order Processor (Local) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Web dashboard for monitoring
- Database storage option (SQLite/PostgreSQL)
- Multi-threading for faster processing
- Docker containerization
- Webhook notifications for new orders

## [1.0.0] - 2024-01-15

### Added
- Initial release of Gmail Order Processor (Local Version)
- IMAP-based Gmail authentication using App Passwords
- Continuous polling of Gmail for order confirmation emails
- Local file-based storage for duplicate email tracking
- Integration with inFlow inventory management system
- Auto-shutdown feature after configurable hours of inactivity
- Comprehensive logging to console and file
- Real-time monitoring and statistics
- Email parsing for billing/shipping addresses and line items
- Customer lookup by company name in inFlow
- Product validation by SKU in inFlow
- Automatic sales order creation in inFlow
- Rate limiting to prevent API throttling
- Processing lock mechanism to prevent race conditions
- Graceful shutdown with cleanup and statistics
- Configuration management with environment variables
- Startup script with validation and error checking

### Features
- **Gmail Integration**
  - IMAP authentication with username/password
  - Search for emails with "Order Placed" in subject
  - Configurable search timeframe (default 7 days)
  - Email content parsing and extraction

- **Order Processing**
  - Extract billing and shipping addresses
  - Parse line items with SKU, description, quantity, price
  - Customer matching by company name
  - Product validation and lookup
  - Automatic order creation in inFlow

- **Duplicate Prevention**
  - Local JSON file tracking of processed emails
  - Processing locks to prevent concurrent processing
  - Unique email identification and tracking

- **Auto-Shutdown**
  - Configurable inactivity timeout (default 2 hours)
  - Smart activity detection (actual processing vs polling)
  - Warning notifications before shutdown
  - Graceful shutdown with cleanup

- **Monitoring & Logging**
  - Real-time console logging
  - File logging to `local_order_monitor.log`
  - Processing statistics and metrics
  - Error tracking and reporting
  - Activity timestamps and duration tracking

- **Configuration**
  - Environment variable configuration
  - `.env` file support with python-dotenv
  - Configurable polling intervals
  - Adjustable logging levels
  - Optional settings with sensible defaults

### Documentation
- Comprehensive README with quick start guide
- Detailed SETUP.md with step-by-step instructions
- QUICK_START.md for common tasks and reference
- Contributing guidelines and development setup
- Example environment configuration file
- MIT License

### Dependencies
- `requests` - HTTP client for inFlow API
- `python-dotenv` - Environment file loading (optional)
- Standard library modules for IMAP, JSON, logging, etc.

### System Requirements
- Python 3.8 or higher
- Gmail account with 2-Factor Authentication
- Gmail App Password
- inFlow inventory system with API access
- Local file system write permissions

### Security
- No OAuth complexity - uses Gmail App Passwords
- Local storage only - no cloud dependencies
- Environment variable configuration for credentials
- Secure IMAP SSL connections
- API key protection and rate limiting

---

## Release Notes

### v1.0.0 - Initial Release

This is the initial release of the Gmail Order Processor Local Version. It provides a complete solution for automatically processing Gmail order confirmation emails and creating sales orders in inFlow inventory management system.

**Key Benefits:**
- Simple setup compared to cloud version (no OAuth or Google Cloud setup)
- Runs locally with full control and visibility
- Auto-shutdown prevents resource waste
- Comprehensive logging for troubleshooting
- Duplicate prevention ensures data integrity

**Perfect for:**
- Development and testing
- Small to medium scale operations
- Users who prefer local control over cloud services
- Organizations with security policies against cloud processing

**Migration from Cloud Version:**
- No migration needed - this is a standalone alternative
- Uses the same order processing logic and inFlow integration
- Can run alongside cloud version if needed