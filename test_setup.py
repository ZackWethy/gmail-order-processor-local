#!/usr/bin/env python3
"""
Setup validation script for Gmail Order Processor (Local)

This script tests all components to ensure the system is properly configured
and ready to process order emails.
"""

import sys
import os
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Python module imports...")
    
    try:
        import requests
        logger.info("✓ requests module available")
    except ImportError:
        logger.error("✗ requests module missing - install with: pip install requests")
        return False
    
    try:
        import dotenv
        logger.info("✓ python-dotenv module available")
    except ImportError:
        logger.warning("⚠ python-dotenv module missing (optional) - install with: pip install python-dotenv")
    
    # Test local module imports
    try:
        from local_config import load_local_config
        logger.info("✓ local_config module can be imported")
    except ImportError as e:
        logger.error(f"✗ local_config import failed: {e}")
        return False
    
    try:
        from local_gmail_service import LocalGmailService
        logger.info("✓ local_gmail_service module can be imported")
    except ImportError as e:
        logger.error(f"✗ local_gmail_service import failed: {e}")
        return False
    
    try:
        from local_storage import LocalEmailStorage
        logger.info("✓ local_storage module can be imported")
    except ImportError as e:
        logger.error(f"✗ local_storage import failed: {e}")
        return False
    
    try:
        from order_processor import OrderProcessor
        logger.info("✓ order_processor module can be imported")
    except ImportError as e:
        logger.error(f"✗ order_processor import failed: {e}")
        return False
    
    try:
        from inflow_api import InflowAPI, InflowConfig
        logger.info("✓ inflow_api module can be imported")
    except ImportError as e:
        logger.error(f"✗ inflow_api import failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading."""
    logger = logging.getLogger(__name__)
    logger.info("Testing configuration...")
    
    try:
        from local_config import load_local_config
        config = load_local_config()
        logger.info("✓ Configuration loaded successfully")
        
        # Check for required settings (will raise exception if missing)
        required_fields = ['gmail_username', 'gmail_password', 'inflow_api_key', 'inflow_company_id']
        for field in required_fields:
            if config.get(field):
                logger.info(f"✓ {field} is configured")
            else:
                logger.error(f"✗ {field} is missing")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

def test_gmail_connection():
    """Test Gmail IMAP connection."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Gmail connection...")
    
    try:
        from local_gmail_service import LocalGmailService
        from local_config import load_local_config
        
        config = load_local_config()
        
        with LocalGmailService(config.get('gmail_username'), config.get('gmail_password')) as gmail:
            logger.info("✓ Gmail IMAP connection successful")
            
            # Test searching for emails
            message_ids = gmail.search_order_emails(since_days=30)
            logger.info(f"✓ Found {len(message_ids)} order emails in last 30 days")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Gmail connection test failed: {e}")
        logger.error("Make sure you're using a Gmail App Password, not your regular password")
        return False

def test_inflow_connection():
    """Test inFlow API connection."""
    logger = logging.getLogger(__name__)
    logger.info("Testing inFlow API connection...")
    
    try:
        from inflow_api import InflowAPI, InflowConfig
        from local_config import load_local_config
        
        config = load_local_config()
        
        inflow_client = InflowAPI(
            InflowConfig(
                api_key=config.get('inflow_api_key'),
                company_id=config.get('inflow_company_id')
            )
        )
        
        # Test getting customers (basic API connectivity test)
        customers = inflow_client.get_customers()
        if customers is not None:
            logger.info("✓ inFlow API connection successful")
            if isinstance(customers, list):
                logger.info(f"✓ Found {len(customers)} customers")
            elif isinstance(customers, dict) and 'data' in customers:
                logger.info(f"✓ Found {len(customers['data'])} customers")
            return True
        else:
            logger.error("✗ inFlow API returned no data")
            return False
            
    except Exception as e:
        logger.error(f"✗ inFlow API test failed: {e}")
        logger.error("Check your inFlow API key and company ID")
        return False

def test_local_storage():
    """Test local storage functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing local storage...")
    
    try:
        from local_storage import LocalEmailStorage
        
        # Use a test directory
        storage = LocalEmailStorage("test_storage")
        
        # Test basic operations
        test_email_id = "test-email-123"
        test_order_id = "test-order-456"
        test_exec_id = "test-exec-789"
        
        # Test processing check
        is_processed = storage.is_email_processed(test_email_id)
        logger.info(f"✓ Email processing check works (result: {is_processed})")
        
        # Test marking as processed
        storage.mark_email_processed(test_email_id, test_order_id, test_exec_id)
        logger.info("✓ Email marking as processed works")
        
        # Test statistics
        stats = storage.get_stats()
        logger.info(f"✓ Storage statistics work: {stats['total_processed_emails']} emails tracked")
        
        # Cleanup test directory
        import shutil
        shutil.rmtree("test_storage", ignore_errors=True)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Local storage test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files are present."""
    logger = logging.getLogger(__name__)
    logger.info("Testing file structure...")
    
    required_files = [
        'local_main.py',
        'local_gmail_service.py',
        'local_storage.py',
        'local_config.py',
        'order_processor.py',
        'inflow_api.py',
        'run_local.py',
        'requirements.txt',
        '.env.example'
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            logger.info(f"✓ {file} exists")
        else:
            logger.error(f"✗ {file} missing")
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """Run all setup tests."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Gmail Order Processor (Local) - Setup Validation")
    logger.info("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Imports", test_imports),
        ("Configuration", test_configuration),
        ("Local Storage", test_local_storage),
        ("Gmail Connection", test_gmail_connection),
        ("inFlow API", test_inflow_connection)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} Test ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nPassed: {passed}, Failed: {failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Your system is ready to process orders.")
        logger.info("Run 'python run_local.py' to start the order processor.")
        return True
    else:
        logger.error(f"❌ {failed} test(s) failed. Please fix the issues above before running the order processor.")
        logger.error("See SETUP.md for detailed configuration instructions.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)