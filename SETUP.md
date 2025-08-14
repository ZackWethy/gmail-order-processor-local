# Local Gmail Order Processor Setup

This guide will help you set up a local version of the Gmail Order Processor that continuously polls Gmail for new order emails and processes them into your inFlow inventory system.

## Overview

The local version uses:
- **IMAP authentication** with Gmail username/password (App Password)
- **Continuous polling** instead of Cloud Functions
- **Local file storage** for duplicate tracking
- **No OAuth setup required**

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Gmail account** with 2-Factor Authentication enabled
3. **inFlow API access** with your API key and Company ID
4. **Basic command line familiarity**

## Step 1: Gmail App Password Setup

Since this uses IMAP authentication, you need to create a Gmail App Password:

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Navigate to **Security** → **2-Step Verification**
3. Scroll down to **App passwords**
4. Click **Select app** → Choose **Mail**
5. Click **Select device** → Choose **Other** → Enter "Order Processor"
6. Click **Generate**
7. **Save the 16-character password** - you'll need this for `GMAIL_PASSWORD`

⚠️ **Important**: You must use the App Password, not your regular Gmail password!

## Step 2: Get inFlow API Credentials

1. Log into your inFlow account
2. Go to **Settings** → **API**
3. Copy your **API Key**
4. Copy your **Company ID**

## Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r local_requirements.txt

# Alternative: Install dependencies individually
pip install requests python-dotenv
```

## Step 4: Configuration

### Option A: Environment File (Recommended)

1. Copy the example environment file:
```bash
cp env.local.example .env.local
```

2. Edit `.env.local` with your actual values:
```bash
# Required Gmail settings
GMAIL_USERNAME=your-email@gmail.com
GMAIL_PASSWORD=your-16-character-app-password

# Required inFlow settings  
INFLOW_API_KEY=your-inflow-api-key
INFLOW_COMPANY_ID=your-inflow-company-id

# Optional: Adjust polling frequency (seconds)
POLL_INTERVAL=60

# Optional: How many days back to search
SEARCH_DAYS=7
```

### Option B: Environment Variables

Set environment variables directly:
```bash
export GMAIL_USERNAME="your-email@gmail.com"
export GMAIL_PASSWORD="your-16-character-app-password"
export INFLOW_API_KEY="your-inflow-api-key"
export INFLOW_COMPANY_ID="your-inflow-company-id"
```

## Step 5: Test Your Setup

### Test Gmail Connection
```bash
python local_gmail_service.py
```
Expected output:
```
✓ Successfully connected to Gmail IMAP
✓ Found X order emails in last 30 days
✓ Successfully retrieved message: Order Placed...
```

### Test Configuration
```bash
python local_config.py
```
Expected output:
```
✓ Configuration loaded successfully
Current Configuration:
  gmail_username: your-email@gmail.com
  gmail_password: abcd****wxyz
  inflow_api_key: sk_****1234
  ...
```

### Test Storage
```bash
python local_storage.py
```
Expected output:
```
✓ Local storage test completed
```

## Step 6: Run the Order Processor

Start the continuous monitoring:
```bash
python local_main.py
```

You should see output like:
```
2024-01-15 10:30:00 - __main__ - INFO - Local Gmail Order Monitor Starting
2024-01-15 10:30:00 - __main__ - INFO - Configuration:
2024-01-15 10:30:00 - __main__ - INFO -   - Gmail User: your-email@gmail.com
2024-01-15 10:30:00 - __main__ - INFO -   - Poll Interval: 60 seconds
2024-01-15 10:30:00 - __main__ - INFO - Starting email monitoring loop...
2024-01-15 10:30:00 - __main__ - INFO - Press Ctrl+C to stop
```

## How It Works

1. **Continuous Polling**: Every 60 seconds (configurable), the system checks Gmail for new "Order Placed" emails
2. **Duplicate Prevention**: Uses local file storage to track processed emails and prevent duplicates
3. **Order Processing**: Extracts order data from emails using the same logic as the Cloud version
4. **inFlow Integration**: Creates orders in inFlow using the same API integration
5. **Auto-Shutdown**: Automatically stops after 2 hours (configurable) of no email processing activity

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `POLL_INTERVAL` | 60 | Seconds between Gmail checks |
| `SEARCH_DAYS` | 7 | How many days back to search for emails |
| `LOG_LEVEL` | INFO | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `STORAGE_DIR` | local_data | Directory for storing processed email tracking |
| `MAX_EMAILS_PER_CHECK` | 10 | Maximum emails to process per check |
| `AUTO_SHUTDOWN_HOURS` | 2.0 | Hours of no email processing before auto-shutdown (0 to disable) |

## Monitoring and Logs

### View Real-time Logs
The system logs to both console and `local_order_monitor.log`:
```bash
# Follow logs in real-time
tail -f local_order_monitor.log
```

### Check Processed Emails
```bash
# View processed emails data
cat local_data/processed_emails.json
```

### Storage Statistics
The system will show statistics when you stop it (Ctrl+C):
```
=== Final Statistics ===
Runtime: 2:30:15
Emails checked: 150
Orders processed: 5
Errors: 0
Total processed emails: 23
```

## Troubleshooting

### Gmail Connection Issues

**Error**: `Failed to connect to Gmail IMAP`
- **Solution**: Make sure you're using an App Password, not your regular password
- **Check**: 2-Factor Authentication is enabled on your Gmail account

**Error**: `No order emails found`
- **Check**: Email subjects contain exactly "Order Placed"
- **Check**: Emails are in your INBOX (not in spam/other folders)

### inFlow API Issues

**Error**: `Customer not found`
- **Check**: Customer names in emails match names in inFlow exactly
- **Check**: Customers are active in inFlow

**Error**: `Product not found`
- **Check**: SKUs in emails match inFlow product SKUs exactly
- **Check**: Products are active in inFlow

### Performance Issues

**Slow processing**:
- Increase `POLL_INTERVAL` to reduce frequency
- Decrease `SEARCH_DAYS` to search fewer emails
- Check your internet connection

## Auto-Shutdown Feature

The service includes an intelligent auto-shutdown feature to save resources:

### How It Works
- **Tracks Processing Activity**: The system monitors when emails are actually processed (not just checked)
- **2-Hour Default**: After 2 hours of no email processing, the service automatically stops
- **Configurable**: Set `AUTO_SHUTDOWN_HOURS=0` to disable, or adjust the timeout
- **Smart Notifications**: Warns you when shutdown is approaching (within 30 minutes)

### What Counts as "Activity"
- Finding a new order email that hasn't been processed yet
- Successfully creating an order in inFlow
- Processing errors also reset the timer (to handle transient issues)

### What Does NOT Count as "Activity"
- Regular polling checks that find no new emails
- Finding emails that were already processed
- Gmail connection tests

### Example Log Output
```
2024-01-15 12:30:00 - INFO - Auto-shutdown in 0.3 hours (no processing activity since 10:15:23)
2024-01-15 12:45:00 - INFO - Auto-shutdown triggered after 2.0 hours of no email processing activity
```

## Stopping the Service

### Manual Stop
Press `Ctrl+C` to stop the service gracefully. The system will:
1. Finish processing any current emails
2. Clean up temporary locks
3. Show final statistics
4. Close connections properly

### Automatic Stop
The service will automatically stop after the configured inactivity period (default 2 hours). This is useful for:
- **Development**: Prevents forgetting to stop the service
- **Resource Management**: Saves CPU/memory when no orders are coming in
- **Scheduled Operations**: Run during business hours, auto-stop overnight

## Security Notes

1. **App Passwords**: Store your Gmail App Password securely
2. **API Keys**: Never commit your `.env.local` file to version control
3. **File Permissions**: The `local_data/` directory contains sensitive information
4. **Network**: All connections use HTTPS/SSL

## Differences from Cloud Version

| Feature | Cloud Version | Local Version |
|---------|---------------|---------------|
| **Authentication** | OAuth with Google Cloud | IMAP with App Password |
| **Triggering** | Gmail Push Notifications | Continuous polling |
| **Storage** | Google Cloud Storage | Local JSON files |
| **Scaling** | Auto-scaling Cloud Functions | Single process |
| **Monitoring** | Cloud Logging | Local logs + console |

## Next Steps

Once you have the local version working:

1. **Monitor** for a few days to ensure emails are processed correctly
2. **Adjust** polling frequency based on your email volume
3. **Backup** your `local_data/` directory regularly
4. **Consider** setting up the Cloud version for production use

## Support

If you encounter issues:

1. Check the logs for error messages
2. Verify your configuration with the test commands
3. Ensure your Gmail and inFlow credentials are correct
4. Check that your order emails have the expected format

The local version uses the same core order processing logic as the Cloud version, so order format issues will be the same in both versions.