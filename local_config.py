#!/usr/bin/env python3
"""
Local configuration loader for the Gmail Order Processor.

This module handles loading configuration from environment variables
and .env files for local development.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logging.warning("python-dotenv not available. Install with: pip install python-dotenv")


class LocalConfig:
    """Configuration manager for local Gmail order processing."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            env_file (Optional[str]): Path to .env file. If None, will try common locations.
        """
        self.logger = logging.getLogger(__name__)
        
        # Load environment file if available
        if DOTENV_AVAILABLE:
            self._load_env_file(env_file)
        
        # Load and validate configuration
        self.config = self._load_config()
        self._validate_config()
    
    def _load_env_file(self, env_file: Optional[str] = None):
        """Load environment variables from .env file."""
        # Try to find .env file in common locations
        possible_files = []
        
        if env_file:
            possible_files.append(Path(env_file))
        
        # Common .env file locations
        possible_files.extend([
            Path('.env.local'),
            Path('.env'),
            Path('local.env'),
            Path('.env.development')
        ])
        
        for env_path in possible_files:
            if env_path.exists():
                self.logger.info(f"Loading environment from: {env_path}")
                load_dotenv(env_path)
                return
        
        self.logger.info("No .env file found, using system environment variables only")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        # Required Gmail settings
        config['gmail_username'] = os.getenv('GMAIL_USERNAME')
        config['gmail_password'] = os.getenv('GMAIL_PASSWORD')
        
        # Required inFlow settings
        config['inflow_api_key'] = os.getenv('INFLOW_API_KEY')
        config['inflow_company_id'] = os.getenv('INFLOW_COMPANY_ID')
        config['inflow_base_url'] = os.getenv('INFLOW_BASE_URL', 'https://cloudapi.inflowinventory.com')
        
        # Optional polling settings
        config['poll_interval'] = int(os.getenv('POLL_INTERVAL', '60'))
        config['search_days'] = int(os.getenv('SEARCH_DAYS', '7'))
        
        # Optional logging and storage settings
        config['log_level'] = os.getenv('LOG_LEVEL', 'INFO').upper()
        config['storage_dir'] = os.getenv('STORAGE_DIR', 'local_data')
        
        # Advanced settings
        config['max_emails_per_check'] = int(os.getenv('MAX_EMAILS_PER_CHECK', '10'))
        config['lock_timeout_minutes'] = int(os.getenv('LOCK_TIMEOUT_MINUTES', '10'))
        config['auto_shutdown_hours'] = float(os.getenv('AUTO_SHUTDOWN_HOURS', '2.0'))
        
        return config
    
    def _validate_config(self):
        """Validate that required configuration is present."""
        required_fields = [
            'gmail_username',
            'gmail_password',
            'inflow_api_key',
            'inflow_company_id'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not self.config.get(field):
                missing_fields.append(field.upper())
        
        if missing_fields:
            self.logger.error("Missing required configuration:")
            for field in missing_fields:
                self.logger.error(f"  - {field}")
            
            self.logger.error("\nPlease set these environment variables or create a .env.local file")
            self.logger.error("See env.local.example for the required format")
            
            if 'GMAIL_PASSWORD' in missing_fields:
                self.logger.error("\nIMPORTANT: For Gmail, you must use an App Password, not your regular password!")
                self.logger.error("To create an App Password:")
                self.logger.error("1. Go to https://myaccount.google.com/")
                self.logger.error("2. Navigate to Security > 2-Step Verification")
                self.logger.error("3. Scroll down to 'App passwords'")
                self.logger.error("4. Generate a password for 'Mail' application")
                self.logger.error("5. Use that 16-character password as GMAIL_PASSWORD")
            
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        # Validate ranges
        if self.config['poll_interval'] < 10:
            self.logger.warning("Poll interval is very low (<10 seconds). This may cause rate limiting.")
        
        if self.config['search_days'] > 30:
            self.logger.warning("Search days is very high (>30 days). This may slow down email searches.")
        
        if self.config['auto_shutdown_hours'] < 0:
            self.logger.warning("Auto-shutdown hours is negative. Auto-shutdown will be disabled.")
        elif self.config['auto_shutdown_hours'] > 0 and self.config['auto_shutdown_hours'] < 0.5:
            self.logger.warning("Auto-shutdown hours is very low (<30 minutes). Service may shutdown frequently.")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key (str): Configuration key
            default (Any): Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary.
        
        Returns:
            Dict[str, Any]: All configuration values
        """
        # Return a copy to prevent modification
        return self.config.copy()
    
    def print_config(self, mask_secrets: bool = True):
        """Print current configuration (for debugging).
        
        Args:
            mask_secrets (bool): Whether to mask sensitive values
        """
        self.logger.info("Current Configuration:")
        
        secret_keys = ['gmail_password', 'inflow_api_key']
        
        for key, value in sorted(self.config.items()):
            if mask_secrets and key in secret_keys:
                if value:
                    masked_value = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}" if len(value) > 8 else "***"
                else:
                    masked_value = "NOT SET"
                self.logger.info(f"  {key}: {masked_value}")
            else:
                self.logger.info(f"  {key}: {value}")


def load_local_config(env_file: Optional[str] = None) -> LocalConfig:
    """Load local configuration.
    
    Args:
        env_file (Optional[str]): Path to .env file
        
    Returns:
        LocalConfig: Configured LocalConfig instance
    """
    return LocalConfig(env_file)


def test_config():
    """Test configuration loading."""
    print("Testing Local Configuration...")
    
    try:
        config = load_local_config()
        print("✓ Configuration loaded successfully")
        
        # Print config (with secrets masked)
        config.print_config(mask_secrets=True)
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the configuration
    logging.basicConfig(level=logging.INFO)
    test_config()