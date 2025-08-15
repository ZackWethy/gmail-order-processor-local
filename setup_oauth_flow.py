#!/usr/bin/env python3
"""
Interactive OAuth 2.0 setup flow for Gmail authentication.
This will guide you through the complete setup process.
"""

import os
import json
import webbrowser
import time
from pathlib import Path

def create_google_cloud_project_guide():
    """Interactive guide for creating Google Cloud project."""
    print("🔧 Step 1: Create Google Cloud Project")
    print("=" * 50)
    print()
    print("I'll open the Google Cloud Console for you...")
    time.sleep(2)
    
    # Open Google Cloud Console
    webbrowser.open("https://console.cloud.google.com/")
    
    print("✅ Browser opened to Google Cloud Console")
    print()
    print("📋 In the browser:")
    print("1. Click 'Select a project' at the top")
    print("2. Click 'NEW PROJECT'")
    print("3. Enter project name: 'Gmail Order Processor'")
    print("4. Click 'CREATE'")
    print("5. Wait for project creation (may take a minute)")
    print()
    
    input("Press ENTER when you've created the project...")
    print()

def enable_gmail_api_guide():
    """Guide for enabling Gmail API."""
    print("🔧 Step 2: Enable Gmail API")
    print("=" * 50)
    print()
    print("Opening Gmail API library page...")
    time.sleep(1)
    
    # Open Gmail API page
    webbrowser.open("https://console.cloud.google.com/apis/library/gmail.googleapis.com")
    
    print("✅ Browser opened to Gmail API page")
    print()
    print("📋 In the browser:")
    print("1. Make sure your new project is selected (top dropdown)")
    print("2. Click the blue 'ENABLE' button")
    print("3. Wait for API to be enabled")
    print()
    
    input("Press ENTER when you've enabled Gmail API...")
    print()

def create_oauth_credentials_guide():
    """Guide for creating OAuth credentials."""
    print("🔧 Step 3: Create OAuth 2.0 Credentials")
    print("=" * 50)
    print()
    print("Opening credentials page...")
    time.sleep(1)
    
    # Open credentials page
    webbrowser.open("https://console.cloud.google.com/apis/credentials")
    
    print("✅ Browser opened to credentials page")
    print()
    print("📋 In the browser:")
    print("1. Click '+ CREATE CREDENTIALS' at the top")
    print("2. Select 'OAuth client ID'")
    print("3. If prompted about consent screen:")
    print("   - Click 'CONFIGURE CONSENT SCREEN'")
    print("   - Choose 'External' (for personal Gmail)")
    print("   - Fill in required fields:")
    print("     • App name: 'Gmail Order Processor'")
    print("     • User support email: your email")
    print("     • Developer contact: your email")
    print("   - Click 'SAVE AND CONTINUE' through the steps")
    print("   - Go back to 'Credentials' tab")
    print("4. Click '+ CREATE CREDENTIALS' > 'OAuth client ID' again")
    print("5. Choose 'Desktop application'")
    print("6. Name: 'Gmail Order Processor Local'")
    print("7. Click 'CREATE'")
    print()
    
    input("Press ENTER when you've created the OAuth credentials...")
    print()

def download_credentials_guide():
    """Guide for downloading credentials."""
    print("🔧 Step 4: Download Credentials File")
    print("=" * 50)
    print()
    print("📋 After creating OAuth credentials:")
    print("1. A popup should appear with 'Download JSON'")
    print("2. Click 'DOWNLOAD JSON'")
    print("3. Save the file to your Downloads folder")
    print()
    print("If the popup disappeared:")
    print("1. Go back to the credentials page")
    print("2. Find your 'Gmail Order Processor Local' credential")
    print("3. Click the download icon (⬇️) on the right")
    print()
    
    input("Press ENTER when you've downloaded the JSON file...")
    print()
    
    # Help user move the file
    print("🔧 Step 5: Move Credentials File")
    print("=" * 30)
    print()
    
    downloads_dir = Path.home() / "Downloads"
    current_dir = Path.cwd()
    
    print(f"Current directory: {current_dir}")
    print(f"Looking for JSON files in: {downloads_dir}")
    print()
    
    # Look for recently downloaded JSON files
    if downloads_dir.exists():
        json_files = list(downloads_dir.glob("client_secret_*.json"))
        if json_files:
            # Sort by modification time, get most recent
            json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            latest_file = json_files[0]
            
            print(f"Found recent credential file: {latest_file.name}")
            
            # Ask if they want to move it automatically
            response = input("Should I move this file to 'credentials.json' in the current directory? (y/n): ")
            if response.lower().startswith('y'):
                import shutil
                shutil.move(str(latest_file), current_dir / "credentials.json")
                print("✅ Credentials file moved to 'credentials.json'")
                return True
            else:
                print(f"Please manually rename and move {latest_file.name} to:")
                print(f"  {current_dir / 'credentials.json'}")
        else:
            print("❌ No credential files found in Downloads")
            print("Please manually copy the downloaded JSON file to:")
            print(f"  {current_dir / 'credentials.json'}")
    else:
        print("Please manually copy the downloaded JSON file to:")
        print(f"  {current_dir / 'credentials.json'}")
    
    return False

def test_oauth_flow():
    """Test the OAuth authentication flow."""
    print("\n🔧 Step 6: Test OAuth Authentication")
    print("=" * 50)
    print()
    
    if not os.path.exists("credentials.json"):
        print("❌ credentials.json not found")
        print("Please make sure the credentials file is in the current directory")
        return False
    
    print("🚀 Starting OAuth authentication flow...")
    print()
    print("What will happen next:")
    print("1. Your browser will open automatically")
    print("2. You'll see a Google sign-in page")
    print("3. Sign in with your Gmail account")
    print("4. Google will ask for permissions")
    print("5. Click 'Allow' to grant access")
    print("6. You'll see a success message")
    print("7. The browser will close and authentication is complete")
    print()
    
    input("Press ENTER to start the authentication flow...")
    
    try:
        from gmail_oauth_service import GmailOAuthService
        
        print("🔐 Starting OAuth flow...")
        gmail = GmailOAuthService()
        
        if gmail.test_connection():
            print("🎉 SUCCESS! OAuth authentication completed!")
            print("✅ Gmail API connection working")
            
            # Test email search
            print("\n📧 Testing email search...")
            message_ids = gmail.search_order_emails(since_days=30)
            print(f"✅ Found {len(message_ids)} order emails in last 30 days")
            
            return True
        else:
            print("❌ OAuth authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during OAuth flow: {str(e)}")
        return False

def main():
    """Main setup flow."""
    print("🚀 Gmail OAuth 2.0 Interactive Setup")
    print("=" * 60)
    print()
    print("This will guide you through setting up Gmail authentication")
    print("using OAuth 2.0. Your browser will open automatically at each step.")
    print()
    print("The process:")
    print("1. Create Google Cloud project")
    print("2. Enable Gmail API")
    print("3. Create OAuth credentials")
    print("4. Download credentials file")
    print("5. Test authentication (browser login)")
    print()
    
    # Check if credentials already exist
    if os.path.exists("credentials.json"):
        print("✅ Found existing credentials.json file")
        response = input("Skip setup and test authentication? (y/n): ")
        if response.lower().startswith('y'):
            if test_oauth_flow():
                print("\n🎉 Setup complete! You can now run the order processor.")
            return
    
    print("Starting interactive setup...")
    print()
    
    # Step 1: Create project
    create_google_cloud_project_guide()
    
    # Step 2: Enable API
    enable_gmail_api_guide()
    
    # Step 3: Create credentials
    create_oauth_credentials_guide()
    
    # Step 4: Download and move credentials
    credentials_ready = download_credentials_guide()
    
    if not credentials_ready:
        print("\n⚠️  Please ensure credentials.json is in the current directory")
        input("Press ENTER when ready...")
    
    # Step 5: Test OAuth flow
    if test_oauth_flow():
        print("\n🎉 Complete! Your Gmail OAuth setup is working!")
        print("\nNext steps:")
        print("1. Add your inFlow API credentials to .env file")
        print("2. Run the order processor: python main.py")
    else:
        print("\n❌ Setup incomplete. Please check the steps above.")

if __name__ == "__main__":
    main()