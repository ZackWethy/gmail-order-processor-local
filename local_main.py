#!/usr/bin/env python3
"""
Local Gmail Order Processor

This script continuously polls Gmail for new order emails and processes them
into the inFlow inventory system. It uses IMAP authentication with username/password
instead of OAuth, making it suitable for local development and testing.

Usage:
    python local_main.py

Environment Variables Required:
    - GMAIL_USERNAME: Your Gmail email address
    - GMAIL_PASSWORD: Your Gmail App Password (not regular password)
    - INFLOW_API_KEY: Your inFlow API key
    - INFLOW_COMPANY_ID: Your inFlow company ID

Optional Environment Variables:
    - POLL_INTERVAL: Seconds between Gmail checks (default: 60)
    - LOG_LEVEL: Logging level (default: INFO)
    - STORAGE_DIR: Directory for local data storage (default: local_data)
"""

import os
import sys
import time
import signal
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json
from pathlib import Path

# Import our local modules
from local_gmail_service import LocalGmailService
from local_storage import LocalEmailStorage
from local_config import load_local_config
from order_processor import OrderProcessor
from inflow_api import InflowAPI, InflowConfig


class LocalOrderMonitor:
    """Local order monitoring service that polls Gmail for new orders."""
    
    def __init__(self):
        """Initialize the local order monitor."""
        self.logger = logging.getLogger(__name__)
        
        # Load configuration from environment
        self.config = self._load_config()
        
        # Initialize services
        self.storage = LocalEmailStorage(self.config['storage_dir'])
        self.order_processor = OrderProcessor()
        self.gmail_service = None
        self.inflow_client = None
        
        # Runtime tracking
        self.running = False
        self.stats = {
            'start_time': None,
            'emails_checked': 0,
            'orders_processed': 0,
            'errors': 0,
            'last_check': None,
            'last_processing_activity': None
        }
        
        # Auto-shutdown configuration
        self.auto_shutdown_hours = float(self.config.get('auto_shutdown_hours', 2.0))
        self.last_activity_time = datetime.now(timezone.utc)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Local Order Monitor initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration using the local config loader."""
        try:
            config_loader = load_local_config()
            return config_loader.get_all()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _initialize_services(self):
        """Initialize Gmail and inFlow services."""
        try:
            # Initialize Gmail service
            self.logger.info("Connecting to Gmail...")
            self.gmail_service = LocalGmailService(
                self.config['gmail_username'],
                self.config['gmail_password']
            )
            
            # Initialize inFlow client
            self.logger.info("Initializing inFlow API client...")
            self.inflow_client = InflowAPI(
                InflowConfig(
                    api_key=self.config['inflow_api_key'],
                    company_id=self.config['inflow_company_id']
                )
            )
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {str(e)}")
            raise
    
    def start(self):
        """Start the order monitoring loop."""
        self.logger.info("Starting Local Gmail Order Monitor")
        self.logger.info(f"Configuration:")
        self.logger.info(f"  - Gmail User: {self.config['gmail_username']}")
        self.logger.info(f"  - Poll Interval: {self.config['poll_interval']} seconds")
        self.logger.info(f"  - Storage Directory: {self.config['storage_dir']}")
        self.logger.info(f"  - Search Days: {self.config['search_days']}")
        self.logger.info(f"  - Auto-shutdown: {self.auto_shutdown_hours} hours of inactivity")
        
        try:
            # Initialize services
            self._initialize_services()
            
            # Start monitoring
            self.running = True
            self.stats['start_time'] = datetime.now(timezone.utc)
            
            self.logger.info("Starting email monitoring loop...")
            self.logger.info("Press Ctrl+C to stop")
            
            while self.running:
                try:
                    # Check for auto-shutdown condition
                    if self._should_auto_shutdown():
                        self.logger.info(f"Auto-shutdown triggered after {self.auto_shutdown_hours} hours of no email processing activity")
                        break
                    
                    self._check_for_new_orders()
                    self.stats['last_check'] = datetime.now(timezone.utc)
                    
                    # Sleep with interruption check
                    self._interruptible_sleep(self.config['poll_interval'])
                    
                except KeyboardInterrupt:
                    self.logger.info("Received keyboard interrupt, stopping...")
                    break
                except Exception as e:
                    self.stats['errors'] += 1
                    self.logger.error(f"Error in monitoring loop: {str(e)}")
                    self.logger.info(f"Continuing after error... (sleeping {self.config['poll_interval']} seconds)")
                    self._interruptible_sleep(self.config['poll_interval'])
            
        except Exception as e:
            self.logger.error(f"Fatal error in order monitor: {str(e)}")
            raise
        finally:
            self._shutdown()
    
    def _interruptible_sleep(self, duration: int):
        """Sleep for duration seconds, but check for interruption every second."""
        for _ in range(duration):
            if not self.running:
                break
            time.sleep(1)
    
    def _should_auto_shutdown(self) -> bool:
        """Check if the service should auto-shutdown due to inactivity."""
        if self.auto_shutdown_hours <= 0:
            return False  # Auto-shutdown disabled
        
        current_time = datetime.now(timezone.utc)
        time_since_activity = current_time - self.last_activity_time
        hours_since_activity = time_since_activity.total_seconds() / 3600
        
        if hours_since_activity >= self.auto_shutdown_hours:
            return True
        
        # Log periodic status updates about auto-shutdown
        remaining_hours = self.auto_shutdown_hours - hours_since_activity
        if remaining_hours <= 0.5:  # Within 30 minutes of shutdown
            self.logger.info(f"Auto-shutdown in {remaining_hours:.1f} hours (no processing activity since {self.last_activity_time.strftime('%H:%M:%S')})")
        
        return False
    
    def _update_activity_time(self, reason: str = "email processing"):
        """Update the last activity time and log the reason."""
        self.last_activity_time = datetime.now(timezone.utc)
        self.stats['last_processing_activity'] = self.last_activity_time
        self.logger.debug(f"Activity updated: {reason} at {self.last_activity_time.strftime('%H:%M:%S')}")
    
    def _check_for_new_orders(self):
        """Check Gmail for new order emails and process them."""
        exec_id = str(uuid.uuid4())[:8]
        
        try:
            self.logger.debug(f"[{exec_id}] Checking for new order emails...")
            
            # Search for order emails
            message_ids = self.gmail_service.search_order_emails(
                since_days=self.config['search_days']
            )
            
            self.stats['emails_checked'] += len(message_ids)
            
            if not message_ids:
                self.logger.debug(f"[{exec_id}] No order emails found")
                return
            
            self.logger.info(f"[{exec_id}] Found {len(message_ids)} potential order emails")
            
            # Process each email
            new_orders = 0
            for message_id in message_ids:
                try:
                    # Get email content
                    email_message = self.gmail_service.get_message_content(message_id)
                    if not email_message:
                        continue
                    
                    # Check if already processed
                    if self.storage.is_email_processed(email_message.message_id):
                        self.logger.debug(f"[{exec_id}] Email {email_message.message_id} already processed, skipping")
                        continue
                    
                    # Update activity time - we found a new email to process
                    self._update_activity_time("new email found")
                    
                    # Process the order
                    result = self._process_single_email(email_message, exec_id)
                    if result:
                        new_orders += 1
                        self.stats['orders_processed'] += 1
                        
                        # Mark as processed
                        self.storage.mark_email_processed(
                            email_message.message_id,
                            result.get('order_id', 'unknown'),
                            exec_id
                        )
                        
                        # Update activity time for successful order processing
                        self._update_activity_time(f"order {result.get('order_id')} created")
                        
                        self.logger.info(f"[{exec_id}] Successfully processed email into order {result.get('order_id')}")
                    else:
                        # Mark as processed with error to avoid reprocessing
                        self.storage.mark_email_processed(
                            email_message.message_id,
                            'processing-error',
                            exec_id
                        )
                        
                except Exception as e:
                    self.logger.error(f"[{exec_id}] Error processing message {message_id}: {str(e)}")
                    continue
            
            if new_orders > 0:
                self.logger.info(f"[{exec_id}] Processed {new_orders} new orders")
            else:
                self.logger.debug(f"[{exec_id}] No new orders to process")
                
        except Exception as e:
            self.logger.error(f"[{exec_id}] Error checking for new orders: {str(e)}")
    
    def _process_single_email(self, email_message, exec_id: str) -> Optional[Dict[str, Any]]:
        """Process a single email message into an inFlow order."""
        try:
            # Convert email message to the format expected by order_processor
            email_content = {
                'subject': email_message.subject,
                'sender': email_message.sender,
                'body': email_message.body,
                'timestamp': email_message.timestamp
            }
            
            # Process order data
            order_data = self.order_processor.process_order_email(email_content)
            if not order_data:
                self.logger.error(f"[{exec_id}] Failed to process order data from email")
                return None
            
            # Log order details
            items = order_data.get('items', [])
            shipping = order_data.get('shipping_address', {}).get('company', '')
            self.logger.info(f"[{exec_id}] Order details - Items: {len(items)} | Shipping to: {shipping}")
            
            # Find customer
            shipping_company = order_data['shipping_address']['company']
            billing_company = order_data['billing_address']['company']
            
            customer = self.inflow_client.find_customer_by_addresses(shipping_company, billing_company)
            
            if not customer:
                self.logger.error(f"[{exec_id}] Customer not found: {shipping_company}")
                return None
            
            # Create order items
            order_items = []
            line_num = 100
            
            for item in order_data['items']:
                sku = item['sku']
                
                # Find product
                product = self.inflow_client.find_product_by_sku(sku)
                if not product:
                    self.logger.error(f"[{exec_id}] Product not found: {sku}")
                    continue
                
                unit_price = item['unit_price']
                if float(unit_price) == 0:
                    unit_price = product.get('defaultPrice', {}).get('unitPrice', '0')
                
                order_items.append({
                    "salesOrderLineId": str(uuid.uuid4()),
                    "productId": product.get('productId'),
                    "description": item['description'],
                    "quantity": {"standardQuantity": item['quantity']},
                    "unitPrice": unit_price,
                    "lineNum": str(line_num)
                })
                line_num += 100
            
            if not order_items:
                self.logger.error(f"[{exec_id}] No valid items to order")
                return None
            
            # Create inFlow order
            order_id = str(uuid.uuid4())
            transaction_id = f"{exec_id}-{str(uuid.uuid4())[:8]}"
            
            inflow_order = {
                "salesOrderId": order_id,
                "customerId": customer.get('customerId'),
                "source": f"Local Gmail Integration (ID: {transaction_id})",
                "contactName": customer.get('name'),
                "lines": order_items,
                "subTotal": sum(float(item['line_total']) for item in order_data['items']),
                "billingAddress": order_data['billing_address'],
                "shippingAddress": order_data['shipping_address'],
                "shipToCompanyName": order_data['shipping_address']['company']
            }
            
            # Create order in inFlow
            self.logger.info(f"[{exec_id}] Creating order in inFlow - Items: {len(order_items)}")
            result = self.inflow_client.create_sales_order(inflow_order)
            
            if result:
                self.logger.info(f"[{exec_id}] Successfully created order: {order_id}")
                return {'order_id': order_id, 'transaction_id': transaction_id}
            else:
                self.logger.error(f"[{exec_id}] Failed to create order in inFlow")
                return None
                
        except Exception as e:
            self.logger.error(f"[{exec_id}] Error processing email: {str(e)}")
            return None
    
    def _shutdown(self):
        """Shutdown services and cleanup."""
        self.logger.info("Shutting down services...")
        
        try:
            # Close Gmail service
            if self.gmail_service:
                self.gmail_service.close()
            
            # Cleanup old locks
            if self.storage:
                self.storage.cleanup_old_locks()
            
            # Print final stats
            self._print_final_stats()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
        
        self.logger.info("Local Order Monitor stopped")
    
    def _print_final_stats(self):
        """Print final runtime statistics."""
        if self.stats['start_time']:
            runtime = datetime.now(timezone.utc) - self.stats['start_time']
            
            self.logger.info("=== Final Statistics ===")
            self.logger.info(f"Runtime: {runtime}")
            self.logger.info(f"Emails checked: {self.stats['emails_checked']}")
            self.logger.info(f"Orders processed: {self.stats['orders_processed']}")
            self.logger.info(f"Errors: {self.stats['errors']}")
            
            if self.stats['last_check']:
                self.logger.info(f"Last check: {self.stats['last_check']}")
            
            if self.stats['last_processing_activity']:
                time_since_activity = datetime.now(timezone.utc) - self.stats['last_processing_activity']
                self.logger.info(f"Last processing activity: {self.stats['last_processing_activity']} ({time_since_activity} ago)")
            else:
                self.logger.info("No email processing activity during this session")
            
            # Auto-shutdown info
            if self.auto_shutdown_hours > 0:
                self.logger.info(f"Auto-shutdown was configured for {self.auto_shutdown_hours} hours of inactivity")
            
            # Storage stats
            storage_stats = self.storage.get_stats()
            self.logger.info(f"Total processed emails: {storage_stats.get('total_processed_emails', 0)}")


def setup_logging(log_level: str = 'INFO'):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('local_order_monitor.log')
        ]
    )
    
    # Set more restrictive log levels for noisy modules
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def main():
    """Main entry point."""
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Local Gmail Order Monitor Starting")
    logger.info("=" * 50)
    
    try:
        # Create and start monitor
        monitor = LocalOrderMonitor()
        monitor.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()