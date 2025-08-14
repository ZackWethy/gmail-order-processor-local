#!/usr/bin/env python3
"""
Simple startup script for the Local Gmail Order Processor.

This script provides an easy way to start the order processor with
proper error handling and setup validation.
"""

import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required modules are available."""
    missing_modules = []
    
    try:
        import requests
    except ImportError:
        missing_modules.append("requests")
    
    try:
        import dotenv
    except ImportError:
        # dotenv is optional but recommended
        print("Warning: python-dotenv not installed. Environment files (.env) won't be loaded automatically.")
        print("Install with: pip install python-dotenv")
    
    if missing_modules:
        print(f"Error: Missing required modules: {', '.join(missing_modules)}")
        print("Install with: pip install -r local_requirements.txt")
        return False
    
    return True

def check_files():
    """Check if required files exist."""
    required_files = [
        'local_main.py',
        'local_gmail_service.py', 
        'local_storage.py',
        'local_config.py',
        'order_processor.py',
        'inflow_api.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"Error: Missing required files: {', '.join(missing_files)}")
        print("Make sure you're running this from the correct directory.")
        return False
    
    return True

def check_config():
    """Check if configuration looks valid."""
    try:
        from local_config import load_local_config
        config = load_local_config()
        print("✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {str(e)}")
        print("\nTo fix this:")
        print("1. Copy env.local.example to .env.local")
        print("2. Fill in your Gmail and inFlow credentials")
        print("3. Make sure you're using a Gmail App Password")
        return False

def main():
    """Main startup function."""
    print("=" * 60)
    print("Local Gmail Order Processor")
    print("=" * 60)
    
    print("\n1. Checking requirements...")
    if not check_requirements():
        sys.exit(1)
    print("✓ All required modules available")
    
    print("\n2. Checking files...")
    if not check_files():
        sys.exit(1)
    print("✓ All required files found")
    
    print("\n3. Checking configuration...")
    if not check_config():
        sys.exit(1)
    
    print("\n4. Starting order processor...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Import and run the main processor
        from local_main import main as run_processor
        run_processor()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()