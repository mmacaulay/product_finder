"""Test fixtures and helpers for API mocking"""

# Sample DE Product API response structures
SAMPLE_DE_PRODUCT_RESPONSE = {
    'entries': 1,
    'products': [
        {
            'description': 'Test Product Description',
            'brand': 'Test Brand',
            'upc_code': '123456789012',
            'uom': '1 unit',
            'manufacturer_name': 'Test Manufacturer',
            'category': 'Test Category',
            'image': 'https://example.com/product-image.jpg',
        }
    ]
}

SAMPLE_DE_PRODUCT_EMPTY_RESPONSE = {
    'entries': 0,
    'products': []
}

# Test UPC codes
TEST_UPC_EXISTING = '111111111111'
TEST_UPC_NEW = '999999999999'
TEST_UPC_API_SUCCESS = '123456789012'
TEST_UPC_API_EMPTY = '000000000000'


def create_mock_de_product_response(description='Test Product', brand='Test Brand', upc='123456789012', image=None):
    """Helper function to create a mock DE Product API response"""
    product_data = {
        'description': description,
        'brand': brand,
        'upc_code': upc,
        'uom': '1 unit',
        'manufacturer_name': 'Test Manufacturer',
    }
    
    if image:
        product_data['image'] = image
    
    return {
        'entries': 1,
        'products': [product_data]
    }


def create_mock_de_product_empty_response():
    """Helper function to create an empty DE Product API response"""
    return SAMPLE_DE_PRODUCT_EMPTY_RESPONSE

