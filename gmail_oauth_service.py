#!/usr/bin/env python3
"""
Gmail OAuth 2.0 service for accessing Gmail without IMAP.
This uses the official Gmail API with OAuth authentication.
"""

import os
import sys
import json
import base64
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

@dataclass
class EmailMessage:
    """Represents an email message with relevant order information."""
    message_id: str
    subject: str
    sender: str
    body: str
    timestamp: int


class GmailOAuthService:
    """Gmail service using OAuth 2.0 and Gmail API instead of IMAP."""
    
    # Gmail API scopes needed for reading emails
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        """Initialize Gmail OAuth service.
        
        Args:
            credentials_file (str): Path to OAuth 2.0 credentials file
            token_file (str): Path to store/load OAuth tokens
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not GMAIL_API_AVAILABLE:
            raise ImportError(
                "Gmail API dependencies not available. Install with:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
        # Initialize OAuth and Gmail service
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail using OAuth 2.0."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired OAuth token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"OAuth credentials file not found: {self.credentials_file}\n"
                        "You need to download OAuth 2.0 credentials from Google Cloud Console.\n"
                        "See setup instructions for details."
                    )
                
                self.logger.info("Starting OAuth 2.0 authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
                self.logger.info(f"OAuth token saved to {self.token_file}")
        
        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Gmail OAuth service initialized successfully")
    
    def search_order_emails(self) -> List[str]:
        """Search for order emails from today using Gmail API.
        Uses Eastern Time to determine 'today'.
        
        Returns:
            List[str]: List of Gmail message IDs from today
        """
        try:
            # Get today's date in Eastern Time
            from datetime import datetime
            import pytz
            
            eastern = pytz.timezone('US/Eastern')
            today_eastern = datetime.now(eastern).date()
            today_str = today_eastern.strftime("%Y/%m/%d")
            
            # Gmail API search query for today only
            query = f'subject:"Order Placed" after:{today_str}'
            
            self.logger.info(f"Searching for emails with query: {query} (Eastern Time)")
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            self.logger.info(f"Found {len(messages)} order emails from today ({today_str} Eastern)")
            
            return [msg['id'] for msg in messages]
            
        except Exception as e:
            self.logger.error(f"Error searching for order emails: {str(e)}")
            return []
    
    def get_message_content(self, message_id: str) -> Optional[EmailMessage]:
        """Get the content of a specific email message using Gmail API.
        
        Args:
            message_id (str): Gmail message ID
            
        Returns:
            Optional[EmailMessage]: Email message object if successful
        """
        try:
            # Get message details
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            payload = message['payload']
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            
            # Only process order emails
            if "Order Placed" not in subject:
                self.logger.debug(f"Skipping non-order email: {subject}")
                return None
            
            # Extract body
            body = self._extract_body(payload)
            
            # Get timestamp
            timestamp = int(int(message['internalDate']) / 1000)
            
            self.logger.info(f"Retrieved message - Subject: {subject} | From: {sender}")
            
            return EmailMessage(
                message_id=message_id,
                subject=subject,
                sender=sender,
                body=body,
                timestamp=timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Error getting message content for {message_id}: {str(e)}")
            return None
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract text body from Gmail API message payload."""
        body = ""
        
        def extract_text_from_part(part):
            """Recursively extract text from message parts."""
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif part.get('mimeType') == 'multipart/alternative' or part.get('mimeType') == 'multipart/mixed':
                # Recursively process multipart messages
                for subpart in part.get('parts', []):
                    text = extract_text_from_part(subpart)
                    if text:
                        return text
            return ""
        
        # Try to extract from main payload
        if payload.get('parts'):
            # Multipart message
            for part in payload['parts']:
                text = extract_text_from_part(part)
                if text:
                    body += text
        else:
            # Single part message
            body = extract_text_from_part(payload)
        
        return body
    
    def test_connection(self) -> bool:
        """Test Gmail API connection."""
        try:
            # Get user profile to test connection
            profile = self.service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress', 'Unknown')
            self.logger.info(f"Gmail API connection successful for: {email}")
            return True
        except Exception as e:
            self.logger.error(f"Gmail API connection test failed: {str(e)}")
            return False


def setup_oauth_credentials():
    """Guide user through OAuth 2.0 setup."""
    print("🔧 Gmail OAuth 2.0 Setup Guide")
    print("=" * 50)
    print()
    print("To use Gmail API with OAuth 2.0, you need to:")
    print()
    print("1. **Create Google Cloud Project**:")
    print("   • Go to: https://console.cloud.google.com/")
    print("   • Create a new project or select existing one")
    print()
    print("2. **Enable Gmail API**:")
    print("   • In the project, go to 'APIs & Services' > 'Library'")
    print("   • Search for 'Gmail API' and enable it")
    print()
    print("3. **Create OAuth 2.0 Credentials**:")
    print("   • Go to 'APIs & Services' > 'Credentials'")
    print("   • Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
    print("   • Choose 'Desktop application'")
    print("   • Download the JSON file")
    print()
    print("4. **Save Credentials File**:")
    print("   • Rename downloaded file to 'credentials.json'")
    print("   • Place it in the same directory as this script")
    print()
    print("5. **Run Authentication**:")
    print("   • The first time you run this, it will open a browser")
    print("   • Sign in to your Gmail account")
    print("   • Grant permissions")
    print("   • The token will be saved for future use")
    print()
    print("This method is:")
    print("✅ Official Google-supported authentication")
    print("✅ More secure than IMAP")
    print("✅ Works with all Gmail account types")
    print("✅ No need for App Passwords or LSA")


if __name__ == "__main__":
    # Test the OAuth Gmail service
    logging.basicConfig(level=logging.INFO)
    
    if not GMAIL_API_AVAILABLE:
        print("❌ Gmail API dependencies not installed")
        print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)
    
    try:
        if not os.path.exists("credentials.json"):
            print("❌ OAuth credentials file 'credentials.json' not found")
            print()
            setup_oauth_credentials()
            sys.exit(1)
        
        print("🔧 Testing Gmail OAuth 2.0 Service...")
        gmail = GmailOAuthService()
        
        if gmail.test_connection():
            print("✅ Gmail OAuth connection successful!")
            
            # Test searching for emails
            message_ids = gmail.search_order_emails(since_days=30)
            print(f"✅ Found {len(message_ids)} order emails in last 30 days")
            
            if message_ids:
                # Test getting message content
                first_message = gmail.get_message_content(message_ids[0])
                if first_message:
                    print(f"✅ Successfully retrieved message: {first_message.subject[:50]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if "credentials.json" in str(e):
            setup_oauth_credentials()