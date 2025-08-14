import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import fcntl
import time


class LocalEmailStorage:
    """Local file-based storage for tracking processed emails and preventing duplicates."""
    
    def __init__(self, storage_dir: str = "local_data"):
        """Initialize local storage.
        
        Args:
            storage_dir (str): Directory to store data files
        """
        self.logger = logging.getLogger(__name__)
        self.storage_dir = Path(storage_dir)
        
        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(exist_ok=True)
        
        # File paths
        self.processed_emails_file = self.storage_dir / "processed_emails.json"
        self.processing_locks_file = self.storage_dir / "processing_locks.json"
        
        # Initialize files if they don't exist
        self._init_storage_files()
        
        self.logger.info(f"Local storage initialized in: {self.storage_dir.absolute()}")
    
    def _init_storage_files(self):
        """Initialize storage files if they don't exist."""
        if not self.processed_emails_file.exists():
            with open(self.processed_emails_file, 'w') as f:
                json.dump({}, f)
        
        if not self.processing_locks_file.exists():
            with open(self.processing_locks_file, 'w') as f:
                json.dump({}, f)
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Safely load JSON file with file locking."""
        try:
            with open(file_path, 'r') as f:
                # Use file locking to prevent race conditions
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
        except Exception as e:
            self.logger.warning(f"Error loading {file_path}: {str(e)}")
            return {}
    
    def _save_json_file(self, file_path: Path, data: Dict[str, Any]):
        """Safely save JSON file with file locking."""
        try:
            with open(file_path, 'w') as f:
                # Use exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(data, f, indent=2, default=str)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {str(e)}")
            raise
    
    def is_email_processed(self, email_id: str) -> bool:
        """Check if an email has already been processed.
        
        Args:
            email_id (str): Unique email identifier
            
        Returns:
            bool: True if email was already processed, False otherwise
        """
        try:
            processed_emails = self._load_json_file(self.processed_emails_file)
            
            if email_id in processed_emails:
                self.logger.warning(f"Email {email_id} was already processed")
                return True
            
            # Check if there's a processing lock for this email
            locks = self._load_json_file(self.processing_locks_file)
            
            if email_id in locks:
                lock_time = datetime.fromisoformat(locks[email_id]['timestamp'])
                current_time = datetime.now(timezone.utc)
                
                # If lock is older than 5 minutes, consider it stale and remove it
                if (current_time - lock_time).total_seconds() > 300:
                    self.logger.warning(f"Removing stale processing lock for email {email_id}")
                    del locks[email_id]
                    self._save_json_file(self.processing_locks_file, locks)
                    return False
                else:
                    self.logger.warning(f"Email {email_id} is currently being processed by another instance")
                    return True
            
            # Try to acquire processing lock
            return self._acquire_processing_lock(email_id)
            
        except Exception as e:
            self.logger.warning(f"Error checking processed email: {str(e)}")
            # Fail open - better to potentially process twice than miss an order
            return False
    
    def _acquire_processing_lock(self, email_id: str) -> bool:
        """Try to acquire a processing lock for the email.
        
        Args:
            email_id (str): Email ID to lock
            
        Returns:
            bool: True if email is already being processed (should skip), False if lock acquired
        """
        try:
            locks = self._load_json_file(self.processing_locks_file)
            
            # Check if lock already exists
            if email_id in locks:
                return True  # Already being processed
            
            # Acquire lock
            locks[email_id] = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'pid': os.getpid()
            }
            
            self._save_json_file(self.processing_locks_file, locks)
            self.logger.info(f"Acquired processing lock for email {email_id}")
            return False  # Not processed, lock acquired
            
        except Exception as e:
            self.logger.error(f"Error acquiring processing lock for {email_id}: {str(e)}")
            # If we can't acquire lock, assume it's safe to process
            return False
    
    def mark_email_processed(self, email_id: str, order_id: str, exec_id: str):
        """Mark an email as processed with its corresponding order ID.
        
        Args:
            email_id (str): Unique email identifier
            order_id (str): Order ID that was created
            exec_id (str): Execution ID for tracking
        """
        try:
            # Load current processed emails
            processed_emails = self._load_json_file(self.processed_emails_file)
            
            # Add this email
            processed_emails[email_id] = {
                'order_id': order_id,
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'exec_id': exec_id
            }
            
            # Save updated data
            self._save_json_file(self.processed_emails_file, processed_emails)
            
            # Remove processing lock
            self._release_processing_lock(email_id)
            
            self.logger.info(f"Marked email {email_id} as processed with order ID {order_id}")
            
        except Exception as e:
            self.logger.warning(f"Error marking email as processed: {str(e)}")
    
    def _release_processing_lock(self, email_id: str):
        """Release processing lock for an email.
        
        Args:
            email_id (str): Email ID to unlock
        """
        try:
            locks = self._load_json_file(self.processing_locks_file)
            
            if email_id in locks:
                del locks[email_id]
                self._save_json_file(self.processing_locks_file, locks)
                self.logger.debug(f"Released processing lock for email {email_id}")
                
        except Exception as e:
            self.logger.warning(f"Error releasing processing lock for {email_id}: {str(e)}")
    
    def get_processed_emails(self) -> Dict[str, Any]:
        """Get all processed emails for reporting/debugging.
        
        Returns:
            Dict[str, Any]: Dictionary of processed emails with their details
        """
        return self._load_json_file(self.processed_emails_file)
    
    def cleanup_old_locks(self, max_age_minutes: int = 10):
        """Clean up old processing locks that might be stale.
        
        Args:
            max_age_minutes (int): Maximum age of locks in minutes before cleanup
        """
        try:
            locks = self._load_json_file(self.processing_locks_file)
            current_time = datetime.now(timezone.utc)
            cleaned_count = 0
            
            # Find stale locks
            stale_locks = []
            for email_id, lock_info in locks.items():
                lock_time = datetime.fromisoformat(lock_info['timestamp'])
                if (current_time - lock_time).total_seconds() > (max_age_minutes * 60):
                    stale_locks.append(email_id)
            
            # Remove stale locks
            for email_id in stale_locks:
                del locks[email_id]
                cleaned_count += 1
            
            if cleaned_count > 0:
                self._save_json_file(self.processing_locks_file, locks)
                self.logger.info(f"Cleaned up {cleaned_count} stale processing locks")
                
        except Exception as e:
            self.logger.warning(f"Error cleaning up old locks: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dict[str, Any]: Statistics about processed emails and locks
        """
        try:
            processed_emails = self._load_json_file(self.processed_emails_file)
            locks = self._load_json_file(self.processing_locks_file)
            
            return {
                'total_processed_emails': len(processed_emails),
                'active_locks': len(locks),
                'storage_directory': str(self.storage_dir.absolute()),
                'files': {
                    'processed_emails': str(self.processed_emails_file),
                    'processing_locks': str(self.processing_locks_file)
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {'error': str(e)}


def test_local_storage():
    """Test function for local storage functionality."""
    print("Testing Local Storage...")
    
    storage = LocalEmailStorage("test_storage")
    
    # Test email processing workflow
    test_email_id = "test-email-123"
    test_order_id = "order-456"
    test_exec_id = "exec-789"
    
    print(f"1. Checking if email {test_email_id} is processed...")
    is_processed = storage.is_email_processed(test_email_id)
    print(f"   Result: {is_processed}")
    
    if not is_processed:
        print(f"2. Marking email {test_email_id} as processed...")
        storage.mark_email_processed(test_email_id, test_order_id, test_exec_id)
        
        print(f"3. Checking again if email {test_email_id} is processed...")
        is_processed_again = storage.is_email_processed(test_email_id)
        print(f"   Result: {is_processed_again}")
    
    print("4. Getting storage stats...")
    stats = storage.get_stats()
    print(f"   Stats: {json.dumps(stats, indent=2)}")
    
    print("✓ Local storage test completed")


if __name__ == "__main__":
    # Test the local storage
    logging.basicConfig(level=logging.INFO)
    test_local_storage()