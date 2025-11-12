from django.test import TestCase
from graphene.test import Client
from api.graphql.schema import schema
from api.models import Product

class GraphQLQueryTest(TestCase):
    """Test GraphQL queries"""
    
    def setUp(self):
        """Create test products"""
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
        """Test querying with non-existent UPC returns None"""
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