import imaplib
import email
from email.header import decode_header
import re
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import os
from dataclasses import dataclass


@dataclass
class EmailMessage:
    """Represents an email message with relevant order information."""
    message_id: str
    subject: str
    sender: str
    body: str
    timestamp: int
    raw_message: email.message.Message


class LocalGmailService:
    """Gmail service that uses IMAP for local development with username/password auth."""
    
    def __init__(self, username: str, password: str):
        """Initialize Gmail IMAP service with credentials.
        
        Args:
            username (str): Gmail username/email address
            password (str): Gmail app password (not regular password)
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        self.username = username
        self.password = password
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.connection = None
        
        # Connect to Gmail
        self._connect()
        
    def _connect(self):
        """Establish IMAP connection to Gmail."""
        try:
            self.logger.info(f"Connecting to Gmail IMAP for {self.username}")
            
            # Create IMAP connection
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # Login
            self.connection.login(self.username, self.password)
            
            # Select INBOX
            self.connection.select('INBOX')
            
            self.logger.info("Successfully connected to Gmail IMAP")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Gmail IMAP: {str(e)}")
            self.logger.error("Make sure you're using an App Password, not your regular Gmail password")
            self.logger.error("To create an App Password:")
            self.logger.error("1. Go to your Google Account settings")
            self.logger.error("2. Navigate to Security > 2-Step Verification")
            self.logger.error("3. At the bottom, choose App passwords")
            self.logger.error("4. Generate a password for 'Mail'")
            raise
    
    def _reconnect_if_needed(self):
        """Reconnect to IMAP if connection is lost."""
        try:
            # Test connection
            self.connection.noop()
        except Exception:
            self.logger.warning("IMAP connection lost, reconnecting...")
            try:
                if self.connection:
                    self.connection.close()
                    self.connection.logout()
            except Exception:
                pass
            self._connect()
    
    def search_order_emails(self, since_days: int = 7) -> List[str]:
        """Search for order emails in the last N days.
        
        Args:
            since_days (int): Number of days to look back for emails
            
        Returns:
            List[str]: List of email message IDs
        """
        try:
            self._reconnect_if_needed()
            
            # Calculate date string for IMAP search (format: DD-Mon-YYYY)
            from datetime import datetime, timedelta
            since_date = datetime.now() - timedelta(days=since_days)
            date_str = since_date.strftime("%d-%b-%Y")
            
            # Search for emails with "Order Placed" in subject since the date
            search_criteria = f'(SUBJECT "Order Placed" SINCE {date_str})'
            
            self.logger.debug(f"Searching for emails with criteria: {search_criteria}")
            
            # Search for messages
            status, message_ids = self.connection.search(None, search_criteria)
            
            if status != 'OK':
                self.logger.error(f"Failed to search emails: {status}")
                return []
            
            # Get message IDs
            message_id_list = message_ids[0].split() if message_ids[0] else []
            message_id_strings = [mid.decode('utf-8') for mid in message_id_list]
            
            self.logger.info(f"Found {len(message_id_strings)} order emails in the last {since_days} days")
            
            return message_id_strings
            
        except Exception as e:
            self.logger.error(f"Error searching for order emails: {str(e)}")
            return []
    
    def get_message_content(self, message_id: str) -> Optional[EmailMessage]:
        """Get the content of a specific email message.
        
        Args:
            message_id (str): The IMAP message ID
            
        Returns:
            Optional[EmailMessage]: Email message object if successful, None if failed
        """
        try:
            self._reconnect_if_needed()
            
            # Fetch the email message
            status, message_data = self.connection.fetch(message_id, '(RFC822)')
            
            if status != 'OK':
                self.logger.error(f"Failed to fetch message {message_id}: {status}")
                return None
            
            # Parse the email
            raw_email = message_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract headers
            subject = self._decode_header(email_message.get('Subject', ''))
            sender = self._decode_header(email_message.get('From', ''))
            date_header = email_message.get('Date', '')
            
            # Parse date
            try:
                parsed_date = email.utils.parsedate_to_datetime(date_header)
                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                timestamp = int(parsed_date.timestamp())
            except Exception:
                timestamp = int(time.time())
            
            # Extract body
            body = self._extract_body(email_message)
            
            # Create unique message ID for tracking
            unique_id = f"imap-{message_id}-{timestamp}"
            
            self.logger.info(f"Retrieved message - ID: {unique_id} | Subject: {subject} | From: {sender}")
            
            # Only return order emails
            if "Order Placed" not in subject:
                self.logger.debug(f"Skipping non-order email: {subject}")
                return None
            
            return EmailMessage(
                message_id=unique_id,
                subject=subject,
                sender=sender,
                body=body,
                timestamp=timestamp,
                raw_message=email_message
            )
            
        except Exception as e:
            self.logger.error(f"Error getting message content for {message_id}: {str(e)}")
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header that might be encoded."""
        if not header_value:
            return ""
        
        try:
            decoded_fragments = decode_header(header_value)
            decoded_string = ""
            
            for fragment, encoding in decoded_fragments:
                if isinstance(fragment, bytes):
                    if encoding:
                        decoded_string += fragment.decode(encoding)
                    else:
                        decoded_string += fragment.decode('utf-8', errors='ignore')
                else:
                    decoded_string += fragment
            
            return decoded_string
        except Exception:
            return str(header_value)
    
    def _extract_body(self, email_message: email.message.Message) -> str:
        """Extract text body from email message."""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get text/plain parts
                if content_type == "text/plain":
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        part_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        body += part_body
                    except Exception:
                        continue
        else:
            # Single part message
            content_type = email_message.get_content_type()
            if content_type == "text/plain":
                charset = email_message.get_content_charset() or 'utf-8'
                try:
                    body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
                except Exception:
                    body = str(email_message.get_payload())
        
        return body
    
    def close(self):
        """Close the IMAP connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection.logout()
                self.logger.info("Closed Gmail IMAP connection")
        except Exception as e:
            self.logger.debug(f"Error closing IMAP connection: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def test_gmail_connection():
    """Test function to verify Gmail IMAP connection works."""
    username = os.getenv('GMAIL_USERNAME')
    password = os.getenv('GMAIL_PASSWORD')
    
    if not username or not password:
        print("Please set GMAIL_USERNAME and GMAIL_PASSWORD environment variables")
        return False
    
    try:
        with LocalGmailService(username, password) as gmail:
            print("✓ Successfully connected to Gmail IMAP")
            
            # Search for recent emails
            message_ids = gmail.search_order_emails(since_days=30)
            print(f"✓ Found {len(message_ids)} order emails in last 30 days")
            
            if message_ids:
                # Test fetching the first message
                first_message = gmail.get_message_content(message_ids[0])
                if first_message:
                    print(f"✓ Successfully retrieved message: {first_message.subject[:50]}...")
                else:
                    print("⚠ Could not retrieve message content")
            
        return True
        
    except Exception as e:
        print(f"✗ Gmail connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the Gmail connection
    logging.basicConfig(level=logging.INFO)
    test_gmail_connection()