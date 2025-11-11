from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import DE_Product

class DE_ProductModelTest(TestCase):
    """Test the DE_Product model"""
    
    def setUp(self):
        """Create a test product for use in tests"""
        self.product = DE_Product.objects.create(
            upc_code='123456789012',
            description='Test Product',
            brand='Test Brand',
            uom='1 unit',
            manufacturer_name='Test Manufacturer'
        )
    
    def test_product_creation(self):
        """Test that a product can be created with required fields"""
        self.assertEqual(self.product.upc_code, '123456789012')
        self.assertEqual(self.product.description, 'Test Product')
        self.assertIsNotNone(self.product.created_at)
        self.assertIsNotNone(self.product.updated_at)
    
    def test_product_str_representation(self):
        """Test the string representation returns description"""
        self.assertEqual(str(self.product), 'Test Product')
    
    def test_upc_code_unique_constraint(self):
        """Test that duplicate UPC codes are not allowed"""
        with self.assertRaises(Exception):  # Will raise IntegrityError
            DE_Product.objects.create(
                upc_code='123456789012',  # Duplicate
                description='Another Product'
            )
    
    def test_product_with_optional_fields(self):
        """Test product creation with optional fields"""
        product = DE_Product.objects.create(
            upc_code='987654321098',
            description='Complete Product',
            ingredients='Water, Sugar',
            nutrition='100 calories',
            categories='Food, Beverages',
            website='https://example.com'
        )
        self.assertEqual(product.ingredients, 'Water, Sugar')
        self.assertEqual(product.website, 'https://example.com')
    
    def test_product_update(self):
        """Test updating product fields"""
        self.product.description = 'Updated Product'
        self.product.save()
        updated_product = DE_Product.objects.get(upc_code='123456789012')
        self.assertEqual(updated_product.description, 'Updated Product')
    
    def test_product_deletion(self):
        """Test product deletion"""
        product_id = self.product.id
        self.product.delete()
        self.assertEqual(DE_Product.objects.filter(id=product_id).count(), 0)