import os
import requests
import hmac
import hashlib
import base64
import logging

logger = logging.getLogger(__name__)

class DEProductAPI:
    def __init__(self):
        self.base_url = os.getenv('DE_PRODUCT_API_BASE_URL')
        self.app_key = os.getenv('DE_PRODUCT_APP_KEY')
        self.auth_key = os.getenv('DE_PRODUCT_AUTH_KEY')
        self.field_names = os.getenv('DE_PRODUCT_FIELD_NAMES')
        
        if not self.base_url:
            raise ValueError('DE_PRODUCT_API_BASE_URL environment variable is required')
        if not self.app_key:
            raise ValueError('DE_PRODUCT_APP_KEY environment variable is required')
        if not self.auth_key:
            raise ValueError('DE_PRODUCT_AUTH_KEY environment variable is required')
        if not self.field_names:
            raise ValueError('DE_PRODUCT_FIELD_NAMES environment variable is required')

    def get_product(self, upc_code):
        auth_token = self.make_auth_token(upc_code)
        query_params = {
            'upc_code': upc_code,
            'upcCode': upc_code,
            'app_key': self.app_key,
            'signature': auth_token,  
            'language': 'en',
            'field_names': self.field_names,
        }
        print(query_params)
        logger.debug(f'Querying DE Product API with params: {query_params}')
        response = requests.get(self.base_url, params=query_params)

        if response.status_code != 200:
            raise Exception(f'Failed to get product: {response.status_code} {response.text}')

        result = response.json()
        print(f"API Response structure: {result}")
        logger.debug(f'API Response: {result}')
        if int(result['entries']) > 0:
            return result['products'][0]
        else:
            return None

    def make_auth_token(self, arg):
        sha_hash = hmac.new(self.auth_key.encode('utf-8'), arg.encode('utf-8'), hashlib.sha1)
        return base64.b64encode(sha_hash.digest()).decode('utf-8')