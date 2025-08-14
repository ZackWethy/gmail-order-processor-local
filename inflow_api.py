import uuid
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import time
import random

@dataclass
class InflowConfig:
    """Configuration for inFlow API client.
    
    Attributes:
        api_key (str): The API key for authentication
        company_id (str): Your inFlow account company ID
        base_url (str): Base URL for the API (defaults to production)
    """
    api_key: str
    company_id: str
    base_url: str = "https://cloudapi.inflowinventory.com"

class InflowAPI:
    """Client for interacting with the inFlow API.
    
    This client provides methods for interacting with various inFlow endpoints
    including customers, products, and sales orders.
    """
    
    def __init__(self, config: InflowConfig):
        """Initialize the API client with configuration.
        
        Args:
            config (InflowConfig): Configuration object containing API credentials
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Network diagnostics with increased timeouts
        self.request_timeouts = {
            'connect': 10,  # Reduced from 30 to avoid hanging
            'read': 30      # Reduced from 60 to avoid hanging
        }
        
        # Create session with SSL verification and retry strategy
        self.session = requests.Session()
        retry_strategy = requests.adapters.Retry(
            total=2,  # Reduced from 3 to be more conservative
            backoff_factor=2,  # Increased from 1 to wait 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
            allowed_methods=["GET", "PUT"]  # HTTP methods to retry
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=5,  # Reduced from 10 to limit concurrent connections
            pool_maxsize=5       # Reduced from 10 to limit concurrent connections
        )
        self.session.mount("https://", adapter)
        
        # Updated headers with API version
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json;version=2024-10-01",
            "X-OverrideAllowNegativeInventory": "TRUE"
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 3.0  # Increased from 2.0 to 3.0 seconds between order creations
        
        # API call tracking
        self._api_calls = {
            'products': {},  # SKU -> count
            'customers': {},  # name -> count
            'total_calls': 0,
            'timeouts': 0,   # Track timeout errors
            'dns_errors': 0  # Track DNS resolution errors
        }

    def _track_api_call(self, call_type: str, identifier: str = None):
        """Track API call patterns for analysis."""
        self._api_calls['total_calls'] += 1
        if identifier:
            if call_type not in self._api_calls:
                self._api_calls[call_type] = {}
            self._api_calls[call_type][identifier] = self._api_calls[call_type].get(identifier, 0) + 1
            if self._api_calls[call_type][identifier] > 1:
                self.logger.warning(f"Redundant {call_type} API call for {identifier} (Count: {self._api_calls[call_type][identifier]})")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request with detailed network diagnostics and rate limit handling."""
        start_time = time.time()
        self._track_api_call(method)
        
        try:
            # Add timeouts to the request
            kwargs['timeout'] = (self.request_timeouts['connect'], self.request_timeouts['read'])
            
            # Log request details
            self.logger.debug(f"Making {method} request to {endpoint}")
            
            # Make the request using session
            response = self.session.request(method, endpoint, **kwargs)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                self.logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry.")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, **kwargs)
            
            # Log successful connection details
            duration = time.time() - start_time
            self.logger.debug(f"Request completed in {duration:.2f}s (Status: {response.status_code})")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.SSLError as e:
            self.logger.error(f"SSL Error: {str(e)}")
            if "EOF occurred in violation of protocol" in str(e):
                self.logger.info("Retrying request after SSL error...")
                time.sleep(2)  # Wait before retry
                return self._make_request(method, endpoint, **kwargs)
            raise
            
        except requests.exceptions.ConnectionError as e:
            duration = time.time() - start_time
            self.logger.error(f"Connection error after {duration:.2f}s: {str(e)}")
            
            if "EOF occurred in violation of protocol" in str(e):
                self.logger.info("Retrying request after connection error...")
                time.sleep(2)  # Wait before retry
                return self._make_request(method, endpoint, **kwargs)
            raise
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Request failed after {duration:.2f}s: {str(e)}")
            raise

    def _log_request_stats(self):
        """Log detailed request statistics."""
        self.logger.info("=== Request Statistics ===")
        self.logger.info(f"Total API calls: {self._api_calls['total_calls']}")
        self.logger.info(f"Connection timeouts: {self._api_calls['timeouts']}")
        self.logger.info(f"DNS failures: {self._api_calls['dns_errors']}")
        
        # Calculate error rates
        total_calls = self._api_calls['total_calls']
        if total_calls > 0:
            timeout_rate = (self._api_calls['timeouts'] / total_calls) * 100
            dns_error_rate = (self._api_calls['dns_errors'] / total_calls) * 100
            self.logger.info(f"Timeout rate: {timeout_rate:.1f}%")
            self.logger.info(f"DNS failure rate: {dns_error_rate:.1f}%")

    def _log_api_stats(self):
        """Log API call statistics."""
        self.logger.info("=== API Call Statistics ===")
        self.logger.info(f"Total API calls: {self._api_calls['total_calls']}")
        self.logger.info(f"Timeout errors: {self._api_calls['timeouts']}")
        self.logger.info(f"DNS errors: {self._api_calls['dns_errors']}")
        
        # Log duplicate calls that might indicate inefficient patterns
        if 'customers' in self._api_calls:
            duplicate_customers = {name: count for name, count in self._api_calls['customers'].items() if count > 1}
            if duplicate_customers:
                self.logger.warning(f"Duplicate customer lookups: {duplicate_customers}")

    def get_customers(self) -> Optional[Dict[str, Any]]:
        """Get list of customers from inFlow.
        
        Returns:
            Optional[Dict[str, Any]]: List of customers if successful, None if failed
            
        API Endpoint:
            GET /{companyId}/customers
        """
        try:
            endpoint = f"{self.config.base_url}/{self.config.company_id}/customers"
            return self._make_request('GET', endpoint).json()
        except Exception as e:
            self.logger.error(f"Error getting customers: {str(e)}")
            return None

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer details from inFlow.
        
        Args:
            customer_id (str): The UUID of the customer to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Customer details if successful, None if failed
            
        API Endpoint:
            GET /{companyId}/customers/{customerId}
        """
        try:
            endpoint = f"{self.config.base_url}/{self.config.company_id}/customers/{customer_id}"
            return self._make_request('GET', endpoint).json()
        except Exception as e:
            self.logger.error(f"Error getting customer: {str(e)}")
            return None

    def get_products(self, include=None, count=None, filter=None) -> Optional[Dict[str, Any]]:
        """Get list of products with optional filtering and includes.
        
        Args:
            include (Optional[str]): Comma-separated list of relationships to include
                (e.g., "cost,defaultPrice,inventoryLines")
            count (Optional[int]): Number of results to return per page
            filter (Optional[Dict]): Dictionary of filters to apply
                Supported filters:
                - name
                - description
                - isActive
                - barcode
                - itemType
                - categoryId
                - lastModifiedDateTime
                - smart (full-text search on name, description, category, barcode and SKU)
                
        Returns:
            Optional[Dict[str, Any]]: List of products if successful, None if failed
            
        API Endpoint:
            GET /{companyId}/products
        """
        try:
            endpoint = f"{self.config.base_url}/{self.config.company_id}/products"
            
            # Build query parameters
            params = {}
            if include:
                params['include'] = include
            if count:
                params['count'] = count
            if filter:
                for key, value in filter.items():
                    params[f'filter[{key}]'] = value

            self.logger.info(f"Getting products from: {endpoint}")
            self.logger.debug(f"Query parameters: {params}")
            
            response = requests.get(
                endpoint,
                headers=self.session.headers,
                params=params
            )
            
            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting products: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            return None

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product details from inFlow.
        
        Args:
            product_id (str): The UUID or SKU of the product to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Product details if successful, None if failed
            
        API Endpoint:
            GET /{companyId}/products/{productId}
        """
        try:
            endpoint = f"{self.config.base_url}/{self.config.company_id}/products/{product_id}"
            
            self.logger.info(f"Getting product from: {endpoint}")
            
            response = requests.get(
                endpoint,
                headers=self.session.headers
            )
            
            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting product: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            return None

    def _wait_for_rate_limit(self):
        """Wait if needed to respect rate limiting."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            # Calculate base sleep time
            base_sleep_time = self.min_request_interval - time_since_last_request
            
            # Add jitter (0-1 second) to avoid thundering herd problem
            jitter = random.random()
            sleep_time = base_sleep_time + jitter
            
            self.logger.info(f"Rate limiting: Waiting {sleep_time:.2f} seconds (base: {base_sleep_time:.2f}s, jitter: {jitter:.2f}s)")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()

    def create_sales_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new sales order in inFlow.
        
        Args:
            order_data (Dict[str, Any]): Dictionary containing the order information
                Required fields:
                - customerId: UUID of the customer
                - items: List of items to order
                    - productId: UUID or SKU of the product
                    - quantity: Object containing standardQuantity
                    - unitPrice: Price per unit
                    - lineNum: Line number for ordering
                
        Returns:
            Optional[Dict[str, Any]]: Response data if successful, None if failed
            
        API Endpoint:
            PUT /{companyId}/sales-orders
        """
        try:
            # Wait for rate limiting only before creating orders
            self._wait_for_rate_limit()
            
            # Ensure required fields are present
            if 'salesOrderId' not in order_data:
                order_data['salesOrderId'] = str(uuid.uuid4())
            
            if 'source' not in order_data:
                order_data['source'] = "Gmail Order Integration"
            
            endpoint = f"{self.config.base_url}/{self.config.company_id}/sales-orders"
            
            self.logger.info(f"Creating sales order at: {endpoint}")
            self.logger.debug(f"Request data: {order_data}")
            
            response = requests.put(
                endpoint,
                headers=self.session.headers,
                json=order_data
            )
            
            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response body: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            # Create link to the order in inFlow
            order_id = result.get('salesOrderId')
            order_link = f"https://app.inflowinventory.com/sales-orders/{order_id}"
            self.logger.info(f"Order created successfully - View in inFlow: {order_link}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error creating sales order: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            return None

    def find_customer_by_name(self, name: str, exact_match: bool = False) -> Optional[Dict[str, Any]]:
        """Find a customer by name, optionally requiring an exact match."""
        self.logger.debug(f"Searching for customer: {name} (exact_match={exact_match})")
        self._track_api_call('customers', name)
        
        # First try exact match
        params = {
            'filter[name]': name,
            'page': 1,
            'per_page': 1
        }
        
        endpoint = f"{self.config.base_url}/{self.config.company_id}/customers"
        
        try:
            exact_response = self._make_request('GET', endpoint, headers=self.session.headers, params=params)
            response_data = exact_response.json()
            
            if isinstance(response_data, list):
                matches = response_data
            else:
                matches = response_data.get('data', [])
                
            self.logger.debug(f"Found {len(matches)} exact matches")
            
            if matches and len(matches) > 0:
                customer_data = matches[0]
                customer_name = customer_data.get('name', '')
                # Only return if it's a true exact match (case-insensitive)
                if customer_name.lower() == name.lower():
                    self.logger.info(f"Found exact match: {customer_name}")
                    return customer_data
                else:
                    self.logger.debug(f"Found close match but not exact: {customer_name}")
        
        except Exception as e:
            self.logger.error(f"Error during exact match search: {str(e)}")
            if exact_match:
                raise  # Re-raise if exact match was required
        
        if exact_match:
            self.logger.debug(f"No exact match found for: {name}")
            return None
            
        # Try smart search if exact match fails
        self.logger.debug(f"Attempting smart search for: {name}")
        
        params = {
            'filter[smart]': name,
            'filter[isActive]': 'true',
            'page': 1,
            'per_page': 25
        }
        
        try:
            smart_response = self._make_request('GET', endpoint, headers=self.session.headers, params=params)
            response_data = smart_response.json()
            
            if isinstance(response_data, list):
                matches = response_data
            else:
                matches = response_data.get('data', [])
                
            self.logger.debug(f"Found {len(matches)} potential matches")
            
            if matches:
                scored_matches = []
                search_terms = set(name.lower().split())
                
                for customer_data in matches:
                    customer_name = customer_data.get('name', '')
                    customer_terms = set(customer_name.lower().split())
                    
                    matching_terms = search_terms.intersection(customer_terms)
                    score = len(matching_terms) / len(search_terms)
                    
                    if name.lower() in customer_name.lower():
                        score += 0.5
                        
                    scored_matches.append((score, customer_data))
                
                scored_matches.sort(reverse=True, key=lambda x: x[0])
                
                if scored_matches and scored_matches[0][0] > 0.5:
                    best_match = scored_matches[0][1]
                    self.logger.info(f"Found best match: {best_match.get('name')} (score: {scored_matches[0][0]:.2f})")
                    return best_match
                else:
                    self.logger.debug("No matches with sufficient relevance score")
                    
        except Exception as e:
            self.logger.error(f"Error during smart search: {str(e)}")
            
        self.logger.debug(f"No matches found after searching {len(matches) if 'matches' in locals() else 0} customers")
        return None

    def find_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Find a product by its SKU.
        
        This method searches for a product using the SKU and returns the full product details.
        
        Args:
            sku (str): The SKU of the product to find
        
        Returns:
            Optional[Dict[str, Any]]: Product details if found, None if not found
            
        API Endpoint:
            GET /{companyId}/products?filter[smart]={sku}
        """
        try:
            self._track_api_call('products', sku)
            self.logger.info(f"Searching for product with SKU: {sku}")
            
            endpoint = f"{self.config.base_url}/{self.config.company_id}/products"
            
            # Use smart filter which includes SKU search
            params = {
                'filter[smart]': sku,
                'include': 'defaultPrice,inventoryLines'  # Include pricing and inventory info
            }
            
            response = requests.get(
                endpoint,
                headers=self.session.headers,
                params=params
            )
            
            response.raise_for_status()
            products = response.json()
            
            if not products:
                self.logger.warning(f"No products found matching SKU: {sku}")
                return None
            
            # Look for exact SKU match
            for product in products:
                if product.get('sku') == sku:
                    product_id = product.get('productId')
                    product_link = f"https://app.inflowinventory.com/products/{product_id}"
                    self.logger.info(f"Found product: {product.get('name')} (SKU: {sku}) - View in inFlow: {product_link}")
                    return product
            
            self.logger.warning(f"No exact SKU match found for: {sku}")
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching for product: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            return None

    def get_sales_orders(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get sales orders with optional filtering parameters.
        
        Args:
            params: Optional dictionary of query parameters that can include:
                - filter[orderDate][fromDate]: String in YYYY-MM-DD format
                - filter[orderDate][toDate]: String in YYYY-MM-DD format
                - filter[orderNumber]: String or list of strings
                - filter[isActive]: String ('true' or 'false')
                - include: String of relationships to include (e.g. 'lines,customer')
                
        Returns:
            List of sales order dictionaries
        """
        endpoint = f"{self.config.base_url}/{self.config.company_id}/sales-orders"
        self.logger.info(f"Getting sales orders from: {endpoint}")
        
        try:
            self.logger.debug(f"Request params: {params}")
            response = requests.get(endpoint, headers=self.session.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            orders = data.get('data', data) if isinstance(data, dict) else data
            self.logger.debug(f"Received {len(orders)} orders from API")
            return orders
            
        except Exception as e:
            self.logger.error(f"Error getting sales orders: {str(e)}")
            if isinstance(e, requests.exceptions.HTTPError):
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response text: {e.response.text}")
            return []

    def find_customer_by_addresses(self, shipping_name: str, billing_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a customer by trying shipping address name first, then billing address name.
        
        Args:
            shipping_name: The customer name from shipping address
            billing_name: The customer name from billing address
            
        Returns:
            Customer object if found, None otherwise
            
        Strategy:
            1. Try exact match with shipping name
            2. If no exact match, try smart search with shipping name
            3. If still no match, try exact match with billing name
            4. If no exact match, try smart search with billing name
            5. Return None if no matches found
        """
        self.logger.info(f"Searching for customer - Shipping name: {shipping_name}, Billing name: {billing_name}")
        
        # First try shipping address name
        if shipping_name:
            # Try exact match first
            shipping_customer = self.find_customer_by_name(shipping_name, exact_match=True)
            if shipping_customer:
                self.logger.info(f"Found exact match using shipping name: {shipping_customer.get('name')}")
                return shipping_customer
                
            # Try smart search with shipping name
            shipping_customer = self.find_customer_by_name(shipping_name, exact_match=False)
            if shipping_customer:
                self.logger.info(f"Found smart match using shipping name: {shipping_customer.get('name')}")
                return shipping_customer
        
        # If no match with shipping name, try billing address name
        if billing_name and billing_name != shipping_name:  # Only if different from shipping
            self.logger.info("No match found with shipping name, trying billing name")
            
            # Try exact match first
            billing_customer = self.find_customer_by_name(billing_name, exact_match=True)
            if billing_customer:
                self.logger.info(f"Found exact match using billing name: {billing_customer.get('name')}")
                return billing_customer
                
            # Try smart search with billing name
            billing_customer = self.find_customer_by_name(billing_name, exact_match=False)
            if billing_customer:
                self.logger.info(f"Found smart match using billing name: {billing_customer.get('name')}")
                return billing_customer
        
        self.logger.info("No customer found using either shipping or billing names")
        return None