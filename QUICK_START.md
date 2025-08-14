# Quick Start Guide

## 1. Copy Required Files

Copy these files from `deployment_repo/` to your local directory:

```bash
# Core processing files
cp deployment_repo/order_processor.py .
cp deployment_repo/inflow_api.py .

# Optional: Config (if you want to reuse existing config)
# cp deployment_repo/config.py .
```

## 2. Install Dependencies

```bash
pip install -r local_requirements.txt
```

## 3. Setup Configuration

```bash
# Copy and edit the environment file
cp env.local.example .env.local
# Edit .env.local with your actual credentials
```

## 4. Test Setup

```bash
# Test Gmail connection
python local_gmail_service.py

# Test configuration
python local_config.py

# Test storage
python local_storage.py
```

## 5. Run the Processor

```bash
# Option 1: Direct run
python local_main.py

# Option 2: Using the startup script (recommended)
python run_local.py
```

## File Structure

After setup, your directory should look like:
```
your-local-directory/
├── local_main.py              # Main polling script
├── local_gmail_service.py     # IMAP Gmail service
├── local_storage.py           # Local file storage
├── local_config.py            # Configuration loader
├── run_local.py               # Startup script
├── order_processor.py         # Copied from deployment_repo
├── inflow_api.py              # Copied from deployment_repo
├── .env.local                 # Your configuration
├── local_requirements.txt     # Dependencies
├── LOCAL_SETUP.md             # Full setup guide
└── local_data/                # Created automatically
    ├── processed_emails.json
    └── processing_locks.json
```

## Environment Variables

**Required:**
- `GMAIL_USERNAME` - Your Gmail address
- `GMAIL_PASSWORD` - Your Gmail App Password  
- `INFLOW_API_KEY` - Your inFlow API key
- `INFLOW_COMPANY_ID` - Your inFlow company ID

**Optional:**
- `POLL_INTERVAL=60` - Seconds between checks
- `SEARCH_DAYS=7` - Days back to search
- `LOG_LEVEL=INFO` - Logging level
- `AUTO_SHUTDOWN_HOURS=2.0` - Auto-stop after hours of no activity

## Monitoring

The system will:
- Check Gmail every 60 seconds (configurable)
- Log all activity to console and `local_order_monitor.log`
- Track processed emails in `local_data/processed_emails.json`
- Prevent duplicate processing automatically
- Auto-shutdown after 2 hours of no new email processing

## Stopping

- **Manual**: Press `Ctrl+C` to stop gracefully
- **Automatic**: Stops after 2 hours of no email processing activity
- Both methods show final statistics