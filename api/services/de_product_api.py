import requests
import hmac
import hashlib
import base64
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class DEProductAPI:
    """
    Service for interacting with the DE Product API.
    
    Configuration is managed through Django settings (DE_PRODUCT_CONFIG).
    """
    
    def __init__(self):
        """
        Initialize the DE Product API client.
        
        Raises:
            ValueError: If required configuration is missing
        """
        config = settings.DE_PRODUCT_CONFIG
        
        self.base_url = config.get('base_url')
        self.app_key = config.get('app_key')
        self.auth_key = config.get('auth_key')
        self.field_names = config.get('field_names')
        self.language = config.get('language', 'en')
        
        # Validate required configuration
        if not self.base_url:
            raise ValueError(
                'DE_PRODUCT_API_BASE_URL is required. '
                'Set it in your environment or Django settings.'
            )
        if not self.app_key:
            raise ValueError(
                'DE_PRODUCT_APP_KEY is required. '
                'Set it in your environment or Django settings.'
            )
        if not self.auth_key:
            raise ValueError(
                'DE_PRODUCT_AUTH_KEY is required. '
                'Set it in your environment or Django settings.'
            )
        if not self.field_names:
            raise ValueError(
                'DE_PRODUCT_FIELD_NAMES is required. '
                'Set it in your environment or Django settings.'
            )
        
        logger.info(f"DEProductAPI initialized with base_url: {self.base_url}")

    def get_product(self, upc_code):
        """
        Fetch product data by UPC code.
        
        Args:
            upc_code: The UPC code to look up
            
        Returns:
            Product data dictionary if found, None otherwise
            
        Raises:
            Exception: If the API request fails
        """
        auth_token = self.make_auth_token(upc_code)
        query_params = {
            'upc_code': upc_code,
            'app_key': self.app_key,
            'signature': auth_token,  
            'language': self.language,
            'field_names': self.field_names,
        }

        logger.debug(f'Querying DE Product API with params: {query_params}')
        response = requests.get(self.base_url, params=query_params)

        if response.status_code != 200:
            raise Exception(f'Failed to get product: {response.status_code} {response.text}')

        result = response.json()
        logger.debug(f'API Response: {result}')
        
        if int(result['entries']) > 0:
            return result['products'][0]
        else:
            return None

    def make_auth_token(self, arg):
        """
        Generate HMAC-SHA1 authentication token.
        
        Args:
            arg: The string to sign (typically the UPC code)
            
        Returns:
            Base64-encoded authentication token
        """
        sha_hash = hmac.new(self.auth_key.encode('utf-8'), arg.encode('utf-8'), hashlib.sha1)
        return base64.b64encode(sha_hash.digest()).decode('utf-8')