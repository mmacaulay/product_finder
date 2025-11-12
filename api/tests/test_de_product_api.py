import os
import responses
from api.tests.base import MockedAPITestCase
from api.tests.fixtures import (
    create_mock_de_product_response,
    create_mock_de_product_empty_response,
    TEST_UPC_API_SUCCESS,
)
from api.services.de_product_api import DEProductAPI


class DEProductAPITest(MockedAPITestCase):
    """Test the DEProductAPI service"""
    
    def setUp(self):
        super().setUp()
        # Set up environment variables for API service
        self.base_url = 'https://api.example.com/product'
        self.app_key = 'test_app_key'
        self.auth_key = 'test_auth_key'
        self.field_names = 'description,brand,upc_code'
        
        os.environ['DE_PRODUCT_API_BASE_URL'] = self.base_url
        os.environ['DE_PRODUCT_APP_KEY'] = self.app_key
        os.environ['DE_PRODUCT_AUTH_KEY'] = self.auth_key
        os.environ['DE_PRODUCT_FIELD_NAMES'] = self.field_names
    
    def test_get_product_success(self):
        """Test successful product retrieval from API"""
        mock_response = create_mock_de_product_response(
            description='Test Product',
            brand='Test Brand',
            upc=TEST_UPC_API_SUCCESS
        )
        
        responses.add(
            responses.GET,
            self.base_url,
            json=mock_response,
            status=200
        )
        
        api = DEProductAPI()
        result = api.get_product(TEST_UPC_API_SUCCESS)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['description'], 'Test Product')
        self.assertEqual(result['brand'], 'Test Brand')
        self.assertEqual(result['upc_code'], TEST_UPC_API_SUCCESS)
    
    def test_get_product_empty_response(self):
        """Test API returns empty results"""
        responses.add(
            responses.GET,
            self.base_url,
            json=create_mock_de_product_empty_response(),
            status=200
        )
        
        api = DEProductAPI()
        result = api.get_product(TEST_UPC_API_SUCCESS)
        
        self.assertIsNone(result)
    
    def test_get_product_error_status(self):
        """Test API returns error status code"""
        responses.add(
            responses.GET,
            self.base_url,
            json={'error': 'Not Found'},
            status=404
        )
        
        api = DEProductAPI()
        with self.assertRaises(Exception) as context:
            api.get_product(TEST_UPC_API_SUCCESS)
        
        self.assertIn('Failed to get product', str(context.exception))
        self.assertIn('404', str(context.exception))
    
    def test_get_product_query_parameters(self):
        """Test that correct query parameters are sent to API"""
        mock_response = create_mock_de_product_response()
        
        responses.add(
            responses.GET,
            self.base_url,
            json=mock_response,
            status=200
        )
        
        api = DEProductAPI()
        api.get_product(TEST_UPC_API_SUCCESS)
        
        # Verify the request was made with correct parameters
        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[0].request
        self.assertIn('upc_code', request.url)
        self.assertIn('app_key', request.url)
        self.assertIn('signature', request.url)
        self.assertIn('language', request.url)
        self.assertIn('field_names', request.url)
    
    def test_make_auth_token(self):
        """Test authentication token generation"""
        api = DEProductAPI()
        token = api.make_auth_token('test_upc')
        
        # Token should be a base64 encoded string
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
        
        # Same input should produce same token
        token2 = api.make_auth_token('test_upc')
        self.assertEqual(token, token2)
        
        # Different input should produce different token
        token3 = api.make_auth_token('different_upc')
        self.assertNotEqual(token, token3)
    
    def test_init_missing_environment_variables(self):
        """Test that missing environment variables raise ValueError"""
        # Save original values
        original_base_url = os.environ.get('DE_PRODUCT_API_BASE_URL')
        original_app_key = os.environ.get('DE_PRODUCT_APP_KEY')
        original_auth_key = os.environ.get('DE_PRODUCT_AUTH_KEY')
        original_field_names = os.environ.get('DE_PRODUCT_FIELD_NAMES')
        
        try:
            # Test missing base_url
            if 'DE_PRODUCT_API_BASE_URL' in os.environ:
                del os.environ['DE_PRODUCT_API_BASE_URL']
            with self.assertRaises(ValueError) as context:
                DEProductAPI()
            self.assertIn('DE_PRODUCT_API_BASE_URL', str(context.exception))
            
            # Restore and test missing app_key
            os.environ['DE_PRODUCT_API_BASE_URL'] = self.base_url
            if 'DE_PRODUCT_APP_KEY' in os.environ:
                del os.environ['DE_PRODUCT_APP_KEY']
            with self.assertRaises(ValueError) as context:
                DEProductAPI()
            self.assertIn('DE_PRODUCT_APP_KEY', str(context.exception))
            
            # Restore and test missing auth_key
            os.environ['DE_PRODUCT_APP_KEY'] = self.app_key
            if 'DE_PRODUCT_AUTH_KEY' in os.environ:
                del os.environ['DE_PRODUCT_AUTH_KEY']
            with self.assertRaises(ValueError) as context:
                DEProductAPI()
            self.assertIn('DE_PRODUCT_AUTH_KEY', str(context.exception))
            
            # Restore and test missing field_names
            os.environ['DE_PRODUCT_AUTH_KEY'] = self.auth_key
            if 'DE_PRODUCT_FIELD_NAMES' in os.environ:
                del os.environ['DE_PRODUCT_FIELD_NAMES']
            with self.assertRaises(ValueError) as context:
                DEProductAPI()
            self.assertIn('DE_PRODUCT_FIELD_NAMES', str(context.exception))
        finally:
            # Restore original values
            if original_base_url:
                os.environ['DE_PRODUCT_API_BASE_URL'] = original_base_url
            if original_app_key:
                os.environ['DE_PRODUCT_APP_KEY'] = original_app_key
            if original_auth_key:
                os.environ['DE_PRODUCT_AUTH_KEY'] = original_auth_key
            if original_field_names:
                os.environ['DE_PRODUCT_FIELD_NAMES'] = original_field_names

