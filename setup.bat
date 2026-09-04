@echo off
echo ========================================
echo Gmail Order Processor - Windows Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found! Starting setup...
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and install requirements
echo Installing packages...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)

REM Copy environment template
if not exist .env (
    echo Creating configuration file...
    copy .env.example .env
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo NEXT STEPS:
echo 1. Edit .env file with your inFlow API credentials
echo 2. Run OAuth setup: venv\Scripts\python setup_oauth_flow.py
echo 3. Start the processor: venv\Scripts\python main.py
echo.
echo For detailed help, see INSTALL.md
echo.
pause