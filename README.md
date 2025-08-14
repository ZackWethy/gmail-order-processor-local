# Gmail Order Processor (Local Version)

A local Python application that continuously monitors Gmail for order confirmation emails and automatically creates sales orders in your inFlow inventory management system.

## 🌟 Features

- **Simple Authentication**: Uses Gmail username/password (no OAuth complexity)
- **Continuous Monitoring**: Polls Gmail every minute for new order emails
- **Duplicate Prevention**: Tracks processed emails to avoid creating duplicate orders
- **Auto-Shutdown**: Automatically stops after 2 hours of no email activity
- **Local Storage**: No cloud dependencies - everything runs and stores locally
- **Real-time Logging**: Console and file logging for monitoring and debugging
- **Error Handling**: Robust error handling with detailed logging
- **Configurable**: Easily adjust polling frequency, search timeframe, and more

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- Gmail account with 2-Factor Authentication enabled
- inFlow inventory system with API access
- Gmail App Password (see setup instructions)

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd gmail-order-processor-local

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials (see SETUP.md for details)
nano .env
```

### 4. Run
```bash
# Option 1: Using the startup script (recommended)
python run_local.py

# Option 2: Direct execution
python local_main.py
```

## 📁 Project Structure

```
gmail-order-processor-local/
├── README.md                  # This file
├── SETUP.md                   # Detailed setup instructions
├── QUICK_START.md             # Quick reference guide
├── requirements.txt           # Python dependencies
├── .env.example               # Environment configuration template
├── .gitignore                 # Git ignore file
├── run_local.py               # Startup script with validation
├── local_main.py              # Main application entry point
├── local_gmail_service.py     # Gmail IMAP service
├── local_storage.py           # Local file-based storage
├── local_config.py            # Configuration management
├── order_processor.py         # Email parsing and order extraction
├── inflow_api.py              # inFlow API client
└── local_data/                # Created automatically
    ├── processed_emails.json  # Tracks processed emails
    └── processing_locks.json  # Prevents duplicate processing
```

## ⚙️ Configuration

### Required Environment Variables
- `GMAIL_USERNAME` - Your Gmail email address
- `GMAIL_PASSWORD` - Your Gmail App Password (not regular password!)
- `INFLOW_API_KEY` - Your inFlow API key
- `INFLOW_COMPANY_ID` - Your inFlow company ID

### Optional Settings
- `POLL_INTERVAL=60` - Seconds between Gmail checks
- `SEARCH_DAYS=7` - Days back to search for emails
- `AUTO_SHUTDOWN_HOURS=2.0` - Auto-stop after hours of no activity
- `LOG_LEVEL=INFO` - Logging verbosity

## 🔧 How It Works

1. **Gmail Authentication**: Connects to Gmail using IMAP with App Password
2. **Email Polling**: Searches for emails with "Order Placed" in subject every 60 seconds
3. **Order Extraction**: Parses email content to extract billing/shipping info and line items
4. **Customer Lookup**: Finds matching customers in inFlow by company name
5. **Product Lookup**: Validates SKUs against inFlow inventory
6. **Order Creation**: Creates sales orders in inFlow with extracted data
7. **Duplicate Prevention**: Tracks processed emails to prevent duplicates
8. **Auto-Shutdown**: Stops after 2 hours of no new email processing

## 📊 Monitoring

### Real-time Logs
```bash
# Follow logs in real-time
tail -f local_order_monitor.log
```

### Activity Tracking
The system tracks:
- Emails checked vs emails processed
- Orders successfully created
- Processing errors and warnings
- Last activity timestamp for auto-shutdown

### Final Statistics
When stopped, shows runtime summary:
```
=== Final Statistics ===
Runtime: 2:15:30
Emails checked: 145
Orders processed: 3
Errors: 0
Last processing activity: 2024-01-15 14:23:15
```

## 🛡️ Security

- **App Passwords**: Uses Gmail App Passwords for secure authentication
- **Local Storage**: All data stored locally, no cloud dependencies
- **API Keys**: Environment variables keep credentials secure
- **File Permissions**: Local data directory contains sensitive information

## 🔄 Auto-Shutdown Feature

Intelligent auto-shutdown saves resources:
- **Default**: Stops after 2 hours of no email processing
- **Smart Detection**: Only counts actual email processing, not polling
- **Warnings**: Notifies when shutdown is approaching
- **Configurable**: Adjust timeout or disable completely

## 📋 Email Format Requirements

The system expects order emails with:
- Subject containing "Order Placed"
- Billing address section with company, address, city/state/zip
- Shipping address section with company, address, city/state/zip  
- Item sections with SKU, description, quantity, price, and line total

## 🆚 vs Cloud Version

| Feature | Local Version | Cloud Version |
|---------|---------------|---------------|
| **Setup** | Simple - username/password | Complex - OAuth + Cloud setup |
| **Dependencies** | Python + Gmail App Password | Google Cloud + Pub/Sub + Functions |
| **Triggering** | Continuous polling | Real-time push notifications |
| **Storage** | Local JSON files | Google Cloud Storage |
| **Scaling** | Single process | Auto-scaling serverless |
| **Cost** | Free (except inFlow API) | Google Cloud usage fees |
| **Use Case** | Development, small scale | Production, high volume |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Setup Issues**: See [SETUP.md](SETUP.md) for detailed instructions
- **Quick Reference**: See [QUICK_START.md](QUICK_START.md) for common tasks
- **Gmail Problems**: Usually related to App Password setup
- **inFlow Issues**: Check API credentials and customer/product names

## 🎯 Roadmap

- [ ] Web dashboard for monitoring
- [ ] Database storage option (SQLite/PostgreSQL)
- [ ] Multi-threading for faster processing
- [ ] Email template customization
- [ ] Webhook notifications for new orders
- [ ] Docker containerization

---

**⚠️ Important**: This is the local development version. For production use with high email volumes, consider the cloud-based version with Google Cloud Functions and Pub/Sub.