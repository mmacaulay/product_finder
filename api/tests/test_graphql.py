from django.test import override_settings
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


# Test configuration for DE Product API
TEST_DE_PRODUCT_CONFIG = {
    'base_url': 'https://api.example.com/product',
    'app_key': 'test_app_key',
    'auth_key': 'test_auth_key',
    'field_names': 'description,brand,upc_code',
    'language': 'en',
}


@override_settings(DE_PRODUCT_CONFIG=TEST_DE_PRODUCT_CONFIG)
class GraphQLQueryTest(MockedAPITestCase):
    """Test GraphQL queries"""
    
    def setUp(self):
        """Create test products"""
        super().setUp()
        
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
    
    def test_query_product_with_image_url(self):
        """Test querying a product by UPC that includes image URL from API"""
        # Mock API response with image
        test_image_url = 'https://example.com/test-product-image.jpg'
        mock_response = create_mock_de_product_response(
            description='Product with Image',
            brand='Image Brand',
            upc='333333333333',
            image=test_image_url
        )
        responses.add(
            responses.GET,
            'https://api.example.com/product',
            json=mock_response,
            status=200
        )
        
        query = '''
            query {
                productByUpc(upc: "333333333333") {
                    upcCode
                    name
                    brand
                    imageUrl
                }
            }
        '''
        result = self.client.execute(query)
        self.assertIsNone(result.get('errors'))
        product = result['data']['productByUpc']
        self.assertEqual(product['upcCode'], '333333333333')
        self.assertEqual(product['name'], 'Product with Image')
        self.assertEqual(product['brand'], 'Image Brand')
        self.assertEqual(product['imageUrl'], test_image_url)
        
        # Verify image URL was saved to database
        saved_product = Product.objects.get(upc_code='333333333333')
        self.assertEqual(saved_product.image_url, test_image_url)