# Gmail Order Processor

A local application that monitors Gmail for order emails and automatically creates sales orders in inFlow Inventory using OAuth 2.0 authentication.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. OAuth Setup
```bash
# Run interactive OAuth setup (opens browser)
python setup_oauth_flow.py
```

This will:
- Guide you through creating Google Cloud credentials
- Open your browser for Gmail login
- Save authentication tokens for future use

### 3. Configure inFlow API
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your inFlow credentials
nano .env
```

Add your inFlow API details:
```bash
INFLOW_API_KEY=your-api-key
INFLOW_COMPANY_ID=your-company-id
```

### 4. Run
```bash
python main.py
```

## 📁 Project Structure

```
gmail-order-processor-local/
├── main.py                    # Main application
├── setup_oauth_flow.py        # Interactive OAuth setup
├── gmail_oauth_service.py     # Gmail OAuth service
├── local_storage.py           # Email tracking storage
├── local_config.py            # Configuration management
├── order_processor.py         # Email parsing
├── inflow_api.py              # inFlow API client
├── requirements.txt           # Dependencies
├── .env.example               # Environment template
├── credentials.json           # OAuth credentials (created during setup)
├── token.json                 # OAuth tokens (created during setup)
└── local_data/                # Email tracking (created automatically)
```

## ⚙️ Configuration

### Required Environment Variables
- `INFLOW_API_KEY` - Your inFlow API key
- `INFLOW_COMPANY_ID` - Your inFlow company ID

### Optional Settings
- `POLL_INTERVAL=60` - Seconds between Gmail checks (default: 60)

- `AUTO_SHUTDOWN_HOURS=2.0` - Auto-stop after hours of inactivity (default: 2.0)
- `LOG_LEVEL=INFO` - Logging level (default: INFO)

## 🔐 Authentication

Gmail authentication uses **OAuth 2.0** (no passwords required):

1. **First time**: Run `python setup_oauth_flow.py`
2. **Browser opens**: Sign in to your Gmail account
3. **Grant permissions**: Allow the app to read your Gmail
4. **Tokens saved**: Future runs use saved authentication

## 🔄 How It Works

1. **Polls Gmail** every 60 seconds for today's emails with "Order Placed" in subject (Eastern Time)
2. **Parses order details** from email content
3. **Finds customers/products** in inFlow using the API
4. **Creates sales orders** in inFlow automatically
5. **Tracks processed emails** to prevent duplicates
6. **Auto-shuts down** after 2 hours of no new orders

## 🛑 Stopping

- **Manual**: Press `Ctrl+C` for graceful shutdown
- **Automatic**: Stops after 2 hours of no email processing
- **Statistics**: Shows final runtime stats on shutdown

## 📊 Monitoring

- **Console logging**: Real-time activity display
- **File logging**: Saved to `main.log`
- **Email tracking**: Stored in `local_data/processed_emails.json`
- **Duplicate prevention**: Automatic via email ID tracking

## 🔧 Troubleshooting

### OAuth Issues
```bash
# Re-run OAuth setup if authentication fails
python setup_oauth_flow.py
```

### Missing Credentials
```bash
# Check if files exist
ls -la credentials.json token.json .env
```

### inFlow API Issues
- Verify your API key and Company ID in `.env`
- Check network connectivity
- Review logs for specific error messages

## 📦 Dependencies

Core requirements:
- `requests` - HTTP client for inFlow API
- `python-dotenv` - Environment variable loading
- `google-auth*` - Google OAuth 2.0 libraries
- `google-api-python-client` - Gmail API client

## 🏗️ Development

The application is structured with clear separation:
- **Authentication**: `gmail_oauth_service.py`
- **Business Logic**: `order_processor.py`
- **API Integration**: `inflow_api.py`
- **Persistence**: `local_storage.py`
- **Configuration**: `local_config.py`
- **Orchestration**: `main.py`

Each module is self-contained and can be tested independently.

---

**Note**: This tool requires a Gmail account and inFlow Inventory system with API access.