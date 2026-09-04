# Complete Installation Guide for Beginners

This guide assumes you have never worked with Python projects before. Follow each step carefully.

## 📋 Prerequisites

### 1. Check if Python is Installed
Open Terminal (Mac/Linux) or Command Prompt (Windows) and type:
```bash
python3 --version
```

**If you see a version number (like `Python 3.8.0`)**: ✅ Python is installed, skip to Step 2.

**If you see "command not found" or error**: ❌ Install Python first:
- **Mac**: Install from [python.org](https://www.python.org/downloads/) or use `brew install python3`
- **Windows**: Install from [python.org](https://www.python.org/downloads/) (check "Add to PATH")
- **Linux**: Run `sudo apt install python3 python3-pip python3-venv` (Ubuntu/Debian)

### 2. Check if pip is Installed
```bash
pip3 --version
```
If this fails, install pip: `python3 -m ensurepip --upgrade`

## 🚀 Installation Steps

### Step 1: Download the Project
If you received this as a ZIP file:
1. **Extract the ZIP** to your Desktop or Documents folder
2. **Open Terminal/Command Prompt**
3. **Navigate to the folder**:
   ```bash
   cd /path/to/gmail-order-processor-local
   ```
   
   **Example paths**:
   - Mac: `cd ~/Desktop/gmail-order-processor-local`
   - Windows: `cd C:\Users\YourName\Desktop\gmail-order-processor-local`

### Step 2: Create Virtual Environment
A virtual environment keeps this project's packages separate from your system.

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

**✅ Success**: Your terminal prompt should now show `(venv)` at the beginning.

### Step 3: Install Dependencies
```bash
# Make sure you're in the project folder and venv is active
pip install -r requirements.txt
```

This will install all needed packages. It may take a few minutes.

### Step 4: Gmail OAuth Setup
```bash
python setup_oauth_flow.py
```

This will:
1. **Open your web browser automatically**
2. **Guide you through creating Google credentials** (if needed)
3. **Ask you to sign in to Gmail**
4. **Save authentication tokens**

**Follow the on-screen instructions carefully.**

### Step 5: Configure inFlow API
```bash
# Copy the example configuration
cp .env.example .env

# Edit the configuration file
```

**How to edit `.env` file**:

**Option A - Using a text editor:**
- **Mac**: `open -e .env` or `nano .env`
- **Windows**: `notepad .env`
- **Linux**: `nano .env` or `gedit .env`

**Option B - Any text editor:**
- Open the `.env` file in any text editor (Notepad, TextEdit, etc.)

**Edit these lines with your actual inFlow details**:
```bash
INFLOW_API_KEY=your-actual-api-key-here
INFLOW_COMPANY_ID=your-actual-company-id-here
```

**Save the file** when done.

### Step 6: Run the Order Processor
```bash
python main.py
```

**✅ Success**: You should see output like:
```
Gmail Order Monitor Starting
Configuration:
  - Authentication: OAuth 2.0
  - Poll Interval: 60 seconds
  - Email Search: Only new emails after startup (Eastern Time)
  - Auto-shutdown: 2.0 hours of inactivity
```

The system is now running and checking for orders!

## 🛑 How to Stop

**Method 1**: Press `Ctrl+C` in the terminal
**Method 2**: Close the terminal window
**Method 3**: Wait 2 hours (auto-shutdown)

## 🔄 Running Again Later

When you want to run it again:

```bash
# 1. Navigate to the project folder
cd /path/to/gmail-order-processor-local

# 2. Activate virtual environment
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate     # Windows

# 3. Run the program
python main.py
```

## ❓ Troubleshooting

### "python3: command not found"
- Install Python from [python.org](https://www.python.org/downloads/)
- On Windows, make sure to check "Add to PATH" during installation

### "Permission denied" errors
- On Mac/Linux, try adding `sudo` before commands
- Make sure you have admin rights

### "No module named 'requests'" or similar
- Make sure virtual environment is activated (you should see `(venv)`)
- Run `pip install -r requirements.txt` again

### OAuth browser doesn't open
- Copy the URL from terminal and paste it in your browser manually
- Make sure you're signed in to the correct Gmail account

### "credentials.json not found"
- Run `python setup_oauth_flow.py` again
- Follow the Google Cloud setup steps carefully

### inFlow API errors
- Double-check your API key and Company ID in the `.env` file
- Make sure you have the correct inFlow permissions

## 📞 Getting Help

If you get stuck:
1. **Check the error message** carefully
2. **Make sure each step was completed** in order
3. **Try running the command again** - sometimes temporary network issues cause failures
4. **Check that virtual environment is activated** - you should see `(venv)` in your terminal

## 📁 What Each File Does

- **`main.py`** - The main program that checks Gmail and creates orders
- **`setup_oauth_flow.py`** - Sets up Gmail authentication (run once)
- **`.env`** - Your configuration file (API keys, settings)
- **`venv/`** - Virtual environment folder (don't delete this)
- **`local_data/`** - Stores processed email tracking (created automatically)
- **`credentials.json`** - Gmail authentication credentials (created locally during setup)
- **`token.json`** - Gmail authentication tokens (created locally during setup)

## 🔒 Security Notes

- **Never share your `.env` file** - it contains your API keys
- **Never share `credentials.json` or `token.json`** - they contain your Gmail access
- **Keep these files private** and secure