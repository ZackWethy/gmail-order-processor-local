#!/usr/bin/env python3
"""
Gmail Order Processor using OAuth 2.0 authentication.
Simplified version that only uses OAuth, no IMAP fallback.
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
from gmail_oauth_service import GmailOAuthService
from local_storage import LocalEmailStorage
from local_config import load_local_config
from order_processor import OrderProcessor
from inflow_api import InflowAPI, InflowConfig


class OAuthOrderMonitor:
    """OAuth-based order monitoring service that polls Gmail for new orders."""
    
    def __init__(self):
        """Initialize the OAuth order monitor."""
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
        self.shutdown_requested = False  # More immediate shutdown flag
        self.startup_time = None  # Track when monitoring starts for email filtering
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
        
        self.logger.info("OAuth Order Monitor initialized")
    
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
        if not self.shutdown_requested:
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.logger.info("Will finish processing current operation and exit...")
            self.shutdown_requested = True
            self.running = False
        else:
            # Second signal forces immediate exit
            self.logger.warning("Received second shutdown signal, forcing immediate exit...")
            sys.exit(0)
    
    def _initialize_services(self):
        """Initialize Gmail and inFlow services."""
        try:
            # Check if OAuth credentials exist
            if not os.path.exists("credentials.json"):
                self.logger.error("OAuth credentials not found!")
                self.logger.error("Run: python setup_oauth_flow.py")
                raise FileNotFoundError("credentials.json not found")
            
            # Initialize Gmail service using OAuth
            self.logger.info("Connecting to Gmail using OAuth 2.0...")
            self.gmail_service = GmailOAuthService()
            
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
        self.logger.info("Starting Gmail Order Monitor")
        self.logger.info(f"Configuration:")
        self.logger.info(f"  - Authentication: OAuth 2.0")
        self.logger.info(f"  - Poll Interval: {self.config['poll_interval']} seconds")
        self.logger.info(f"  - Storage Directory: {self.config['storage_dir']}")
        self.logger.info(f"  - Email Search: Only new emails after startup (Eastern Time)")
        self.logger.info(f"  - Auto-shutdown: {self.auto_shutdown_hours} hours of inactivity")
        
        try:
            # Initialize services
            self._initialize_services()
            
            # Start monitoring
            self.running = True
            self.startup_time = datetime.now(timezone.utc)
            self.stats['start_time'] = self.startup_time
            
            self.logger.info("Starting email monitoring loop...")
            self.logger.info(f"📧 Email Filter: Only processing emails received after {self.startup_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            self.logger.info("Press Ctrl+C to stop")
            
            while self.running and not self.shutdown_requested:
                try:
                    # Check for shutdown first
                    if self.shutdown_requested:
                        self.logger.info("Shutdown requested, stopping monitoring loop...")
                        break
                    
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
            if not self.running or self.shutdown_requested:
                self.logger.debug("Sleep interrupted by shutdown request")
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
            
            # Search for order emails using OAuth (only emails received after startup)
            message_ids = self.gmail_service.search_order_emails(since_timestamp=self.startup_time)
            
            self.stats['emails_checked'] += len(message_ids)
            
            if not message_ids:
                self.logger.debug(f"[{exec_id}] No order emails found")
                return
            
            self.logger.info(f"[{exec_id}] Found {len(message_ids)} potential order emails")
            
            # Process each email
            new_orders = 0
            for message_id in message_ids:
                # Check for shutdown between each email
                if self.shutdown_requested:
                    self.logger.info(f"[{exec_id}] Shutdown requested, stopping email processing...")
                    break
                    
                try:
                    # Get email content using OAuth
                    email_message = self.gmail_service.get_message_content(message_id)
                    if not email_message:
                        continue
                    
                    # Double-check: ensure email was received after startup (safety check)
                    if self.startup_time and email_message.timestamp:
                        email_time = datetime.fromtimestamp(email_message.timestamp, tz=timezone.utc)
                        if email_time < self.startup_time:
                            self.logger.debug(f"[{exec_id}] Email {email_message.message_id} received before startup ({email_time} < {self.startup_time}), skipping")
                            continue
                    
                    # Check if already processed
                    if self.storage.is_email_processed(email_message.message_id):
                        self.logger.debug(f"[{exec_id}] Email {email_message.message_id} already processed, skipping")
                        continue
                    
                    # Update activity time - we found a new email to process
                    self._update_activity_time("new email found")
                    
                    # Log when we find a new email that meets our criteria
                    email_time = datetime.fromtimestamp(email_message.timestamp, tz=timezone.utc)
                    self.logger.info(f"[{exec_id}] 📧 Processing new email: {email_message.subject} (received: {email_time.strftime('%Y-%m-%d %H:%M:%S UTC')})")
                    
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
            
            # Batch lookup all products first to improve efficiency
            skus_to_lookup = [item['sku'] for item in order_data['items']]
            self.logger.debug(f"[{exec_id}] Batch lookup for {len(skus_to_lookup)} products: {skus_to_lookup}")
            
            # Check for shutdown before batch operation
            if self.shutdown_requested:
                self.logger.info(f"[{exec_id}] Shutdown requested before product lookup")
                return None
            
            # Use optimized batch lookup if available, otherwise fall back to individual lookups
            if hasattr(self.inflow_client, 'find_products_by_skus_batch') and len(skus_to_lookup) > 1:
                products_map = self.inflow_client.find_products_by_skus_batch(skus_to_lookup)
                # Log missing products from batch result
                for sku in skus_to_lookup:
                    if not products_map.get(sku):
                        self.logger.error(f"[{exec_id}] Product not found: {sku}")
            else:
                # Fall back to individual lookups
                products_map = {}
                for sku in skus_to_lookup:
                    # Check for shutdown between lookups
                    if self.shutdown_requested:
                        self.logger.info(f"[{exec_id}] Shutdown requested during product lookup")
                        return None
                        
                    product = self.inflow_client.find_product_by_sku(sku)
                    if product:
                        products_map[sku] = product
                    else:
                        self.logger.error(f"[{exec_id}] Product not found: {sku}")
            
            # Create order items using the batched results
            order_items = []
            line_num = 100
            
            for item in order_data['items']:
                sku = item['sku']
                
                # Use pre-fetched product data
                if sku not in products_map:
                    continue  # Product not found, already logged
                
                product = products_map[sku]
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
                "source": f"OAuth Gmail Integration (ID: {transaction_id})",
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
            # Cleanup old locks
            if self.storage:
                self.storage.cleanup_old_locks()
            
            # Log API and cache statistics
            if self.inflow_client and hasattr(self.inflow_client, '_log_api_stats'):
                self.inflow_client._log_api_stats()
            
            # Print final stats
            self._print_final_stats()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
        
        self.logger.info("OAuth Order Monitor stopped")
    
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
            logging.FileHandler('oauth_order_monitor.log')
        ]
    )
    
    # Set more restrictive log levels for noisy modules
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)


def main():
    """Main entry point."""
    # Quick setup check
    if not os.path.exists("credentials.json"):
        print("🔧 Gmail OAuth Setup Required")
        print("=" * 40)
        print("Run this command first to set up Gmail authentication:")
        print("  python setup_oauth_flow.py")
        print()
        print("This will open your browser to sign in to Gmail.")
        sys.exit(1)
    
    if not os.path.exists(".env"):
        print("📝 Configuration Required")
        print("=" * 30)
        print("Copy and edit the configuration file:")
        print("  cp .env.example .env")
        print("  # Edit .env with your inFlow API credentials")
        sys.exit(1)
    
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Gmail Order Monitor Starting")
    logger.info("=" * 50)
    
    try:
        # Create and start monitor
        monitor = OAuthOrderMonitor()
        monitor.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()