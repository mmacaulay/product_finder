from api.tests.base import MockedAPITestCase
from api.tests.fixtures import (
    create_mock_de_product_response,
    create_mock_de_product_empty_response,
    TEST_UPC_API_SUCCESS,
    TEST_UPC_API_EMPTY,
)
from graphene.test import Client
from api.graphql.schema import schema
from api.models import Product
import responses
import os

class GraphQLQueryTest(MockedAPITestCase):
    """Test GraphQL queries"""
    
    def setUp(self):
        """Create test products"""
        super().setUp()
        # Set up environment variables for API service
        os.environ['DE_PRODUCT_API_BASE_URL'] = 'https://api.example.com/product'
        os.environ['DE_PRODUCT_APP_KEY'] = 'test_app_key'
        os.environ['DE_PRODUCT_AUTH_KEY'] = 'test_auth_key'
        os.environ['DE_PRODUCT_FIELD_NAMES'] = 'description,brand,upc_code'
        
        self.product1 = Product.objects.create(
            upc_code='111111111111',
            name='Product One',
            brand='Brand A'
        )
        self.product2 = Product.objects.create(
            upc_code='222222222222',
            name='Product Two',
            brand='Brand B'
        )
        self.client = Client(schema)
    
    def test_query_all_products(self):
        """Test querying all products"""
        query = '''
            query {
                allProducts {
                    upcCode
                    name
                    brand
                }
            }
        '''
        result = self.client.execute(query)
        self.assertIsNone(result.get('errors'))
        products = result['data']['allProducts']
        self.assertEqual(len(products), 2)
    
    def test_query_product_by_upc(self):
        """Test querying a product by UPC code"""
        query = '''
            query {
                productByUpc(upc: "111111111111") {
                    upcCode
                    name
                    brand
                }
            }
        '''
        result = self.client.execute(query)
        self.assertIsNone(result.get('errors'))
        product = result['data']['productByUpc']
        self.assertEqual(product['upcCode'], '111111111111')
        self.assertEqual(product['name'], 'Product One')
    
    def test_query_product_by_id(self):
        """Test querying a product by ID"""
        query = f'''
            query {{
                productById(id: {self.product1.id}) {{
                    id
                    upcCode
                    name
                }}
            }}
        '''
        result = self.client.execute(query)
        self.assertIsNone(result.get('errors'))
        product = result['data']['productById']
        self.assertEqual(product['name'], 'Product One')
    
    def test_query_nonexistent_upc(self):
        """Test querying with non-existent UPC returns None when API returns empty"""
        # Mock API to return empty response
        responses.add(
            responses.GET,
            'https://api.example.com/product',
            json=create_mock_de_product_empty_response(),
            status=200
        )
        
        query = '''
            query {
                productByUpc(upc: "999999999999") {
                    upcCode
                }
            }
        '''
        result = self.client.execute(query)
        self.assertIsNone(result.get('errors'))
        self.assertIsNone(result['data']['productByUpc'])
    
    def test_query_product_by_upc_with_api_call(self):
        """Test querying a product by UPC that triggers API call and creates product"""
        # Mock API response
        mock_response = create_mock_de_product_response(
            description='API Product',
            brand='API Brand',
            upc=TEST_UPC_API_SUCCESS
        )
        responses.add(
            responses.GET,
            'https://api.example.com/product',
            json=mock_response,
            status=200
        )
        
        query = f'''
            query {{
                productByUpc(upc: "{TEST_UPC_API_SUCCESS}") {{
                    upcCode
                    name
                    brand
                }}
            }}
        '''
        result = self.client.execute(query)
        self.assertIsNone(result.get('errors'))
        product = result['data']['productByUpc']
        self.assertEqual(product['upcCode'], TEST_UPC_API_SUCCESS)
        self.assertEqual(product['name'], 'API Product')
        self.assertEqual(product['brand'], 'API Brand')
        
        # Verify product was saved to database
        saved_product = Product.objects.get(upc_code=TEST_UPC_API_SUCCESS)
        self.assertEqual(saved_product.name, 'API Product')
        self.assertEqual(saved_product.brand, 'API Brand')
    
    def test_query_product_by_upc_api_error(self):
        """Test querying a product when API returns an error"""
        # Mock API error response
        responses.add(
            responses.GET,
            'https://api.example.com/product',
            json={'error': 'Internal Server Error'},
            status=500
        )
        
        query = f'''
            query {{
                productByUpc(upc: "{TEST_UPC_API_EMPTY}") {{
                    upcCode
                }}
            }}
        '''
        result = self.client.execute(query)
        # Should have an error in the response
        self.assertIsNotNone(result.get('errors'))
    
    def test_query_product_by_upc_api_empty_response(self):
        """Test querying a product when API returns empty results"""
        # Mock API empty response
        responses.add(
            responses.GET,
            'https://api.example.com/product',
            json=create_mock_de_product_empty_response(),
            status=200
        )
        
        query = f'''
            query {{
                productByUpc(upc: "{TEST_UPC_API_EMPTY}") {{
                    upcCode
                }}
            }}
        '''
        result = self.client.execute(query)
        self.assertIsNone(result.get('errors'))
        self.assertIsNone(result['data']['productByUpc'])