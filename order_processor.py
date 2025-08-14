from datetime import datetime
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

@dataclass
class OrderItem:
    sku: str          # The SKU code (e.g., "PCC16")
    description: str  # The description in parentheses
    quantity: str     # String representation of number (e.g., "1")
    unit_price: str  # String representation of price (e.g., "83.70")
    line_total: str  # String representation of line total

@dataclass
class Address:
    company: str
    address1: str
    city: str
    state: str
    postal_code: str
    country: str = "United States"
    deliver_to: str = ""

@dataclass
class Order:
    billing_address: Address
    shipping_address: Address
    items: List[OrderItem]
    customer_email: str

class OrderProcessor:
    def __init__(self):
        # Configure logger with info level
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # Changed from DEBUG to INFO

    def process_order_email(self, email_content) -> Optional[Dict[str, Any]]:
        """Process the order confirmation email content.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing order information in the format:
            {
                "billing_address": {
                    "company": str,
                    "address1": str,
                    "city": str,
                    "state": str,
                    "postalCode": str,
                    "country": str
                },
                "shipping_address": {
                    "company": str,
                    "deliverTo": str,
                    "address1": str,
                    "city": str,
                    "state": str,
                    "postalCode": str,
                    "country": str
                },
                "items": [
                    {
                        "sku": str,
                        "description": str,
                        "quantity": str,
                        "unit_price": str,
                        "line_total": str
                    }
                ]
            }
        """
        if email_content is None:
            return None

        try:
            # Extract addresses
            billing_address = self._extract_billing_address(email_content)
            shipping_address = self._extract_shipping_address(email_content)
            items = self._extract_items(email_content)
            
            # Format the order data to match our test structure
            order_data = {
                "billing_address": {
                    "company": billing_address.company,
                    "address1": billing_address.address1,
                    "city": billing_address.city,
                    "state": billing_address.state,
                    "postalCode": billing_address.postal_code,
                    "country": billing_address.country
                },
                "shipping_address": {
                    "company": shipping_address.company,
                    "deliverTo": shipping_address.deliver_to,
                    "address1": shipping_address.address1,
                    "city": shipping_address.city,
                    "state": shipping_address.state,
                    "postalCode": shipping_address.postal_code,
                    "country": shipping_address.country
                },
                "items": [
                    {
                        "sku": item.sku,
                        "description": item.description,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "line_total": item.line_total
                    }
                    for item in items
                ]
            }
            
            return order_data
            
        except Exception as e:
            self.logger.error(f"Error processing order: {e}")
            return None

    def _extract_billing_address(self, email_content) -> Address:
        """Extract billing address from email content."""
        try:
            body = email_content['body']
            
            # Extract billing address components
            company_match = re.search(r'Bill To:\s*\nCompany:\s*([^\n]+)', body)
            address1_match = re.search(r'Address 1:\s*([^\n]+)', body)
            city_state_zip_match = re.search(r'City/State/Zip:\s*([^,]+),\s*(\w+)\s+(\d{5})', body)
            
            return Address(
                company=company_match.group(1).strip() if company_match else "",
                address1=address1_match.group(1).strip() if address1_match else "",
                city=city_state_zip_match.group(1).strip() if city_state_zip_match else "",
                state=city_state_zip_match.group(2).strip() if city_state_zip_match else "",
                postal_code=city_state_zip_match.group(3).strip() if city_state_zip_match else "",
                country="United States"
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting billing address: {e}")
            return Address("", "", "", "", "")

    def _extract_shipping_address(self, email_content) -> Address:
        """Extract shipping address from email content."""
        try:
            body = email_content['body']
            
            # Updated regex to specifically match the Ship To section
            company_match = re.search(r'Ship To:.*?\nCompany:\s*(.*?)\n', body, re.DOTALL)
            address1_match = re.search(r'Ship To:.*?Address 1:\s*(.*?)\n', body, re.DOTALL)
            city_state_zip_match = re.search(r'Ship To:.*?City/State/Zip:\s*(.*?),\s*(\w+)\s+(\d{5})', body, re.DOTALL)
            
            if not company_match:
                self.logger.error("Could not find shipping company name in email")
                return Address("", "", "", "", "", "")
            
            company_name = company_match.group(1).strip()
            self.logger.info(f"Extracted shipping company name: {company_name}")
            
            return Address(
                company=company_name,
                address1=address1_match.group(1).strip() if address1_match else "",
                city=city_state_zip_match.group(1).strip() if city_state_zip_match else "",
                state=city_state_zip_match.group(2).strip() if city_state_zip_match else "",
                postal_code=city_state_zip_match.group(3).strip() if city_state_zip_match else "",
                country="United States"
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting shipping address: {e}")
            return Address("", "", "", "", "", "")

    def _extract_items(self, email_content) -> List[OrderItem]:
        """Extract ordered items from email content."""
        try:
            body = email_content['body']
            items = []
            
            # Add debug logging for the raw body
            self.logger.debug(f"Processing body:\n{body}")
            
            item_sections = re.finditer(
                r'Item:\s*([^(]+?)\s*\(((?:[^)]|\n(?!Item:))*)\)[\s\n]*'    # SKU and description (allowing newlines in description)
                r'Ordered:\s*(\d+)/\w+\s*@\s*(?:\$([0-9.]+)|N/A)[\s\n]*'    # Quantity and price
                r'Line Total:\s*(?:\$([0-9.]+)|N/A)',                        # Line total
                body,
                re.MULTILINE  # Keep MULTILINE flag
            )
            
            # Convert iterator to list for debugging
            matches = list(item_sections)
            self.logger.debug(f"Found {len(matches)} matches")
            
            for match in matches:
                # Debug log the raw match
                self.logger.debug(f"Raw match: {match.groups()}")
                
                # Clean up description by replacing newlines with spaces
                description = re.sub(r'\s+', ' ', match.group(2).strip())
                
                item = OrderItem(
                    sku=match.group(1).strip(),
                    description=description,
                    quantity=match.group(3),
                    unit_price=match.group(4) if match.group(4) else "0",  # Set to "0" if N/A
                    line_total=match.group(5) if match.group(5) else "0"   # Set to "0" if N/A
                )
                self.logger.info(f"Extracted item: {item.sku} ({item.description}) - Price: {'N/A' if not match.group(4) else match.group(4)}")
                items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error extracting items: {e}")
            self.logger.error(f"Email body: {body if 'body' in locals() else 'Not available'}")
            return []
