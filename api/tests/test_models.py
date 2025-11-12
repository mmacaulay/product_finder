from api.tests.base import MockedAPITestCase
from django.core.exceptions import ValidationError
from ..models import Product

class ProductModelTest(MockedAPITestCase):
    """Test the Product model"""
    
    def setUp(self):
        """Create a test product for use in tests"""
        self.product = Product.objects.create(
            upc_code='123456789012',
            name='Test Product',
            brand='Test Brand',
            de_product_data={
                'description': 'Test Description',
                'uom': '1 unit',
                'manufacturer_name': 'Test Manufacturer'
            }
        )
    
    def test_product_creation(self):
        """Test that a product can be created with required fields"""
        self.assertEqual(self.product.upc_code, '123456789012')
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.brand, 'Test Brand')
        self.assertEqual(self.product.de_product_data, {
            'description': 'Test Description',
            'uom': '1 unit',
            'manufacturer_name': 'Test Manufacturer'
        })
        self.assertIsNotNone(self.product.created_at)
        self.assertIsNotNone(self.product.updated_at)
    
    def test_product_str_representation(self):
        """Test the string representation returns name"""
        self.assertEqual(str(self.product), 'Test Product')
    
    def test_upc_code_unique_constraint(self):
        """Test that duplicate UPC codes are not allowed"""
        with self.assertRaises(Exception):  # Will raise IntegrityError
            Product.objects.create(
                upc_code='123456789012',  # Duplicate
                name='Another Product',
                brand='Another Brand',
            )
    
    def test_product_update(self):
        """Test updating product fields"""
        self.product.name = 'Updated Product'
        self.product.save()
        updated_product = Product.objects.get(upc_code='123456789012')
        self.assertEqual(updated_product.name, 'Updated Product')
    
    def test_product_deletion(self):
        """Test product deletion"""
        product_id = self.product.id
        self.product.delete()
        self.assertEqual(Product.objects.filter(id=product_id).count(), 0)