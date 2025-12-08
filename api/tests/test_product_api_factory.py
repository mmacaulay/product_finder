from django.test import TestCase, override_settings
from api.services.product_api_factory import (
    get_product_api,
    get_product_adapter,
    get_current_api_and_adapter,
)
from api.services.de_product_api import DEProductAPI
from api.services.barcodes_data_api import BarcodesDataAPI
from api.adapters.de_product_adapter import DEProductAdapter
from api.adapters.barcodes_data_adapter import BarcodesDataAdapter


# Test configurations
TEST_DE_PRODUCT_CONFIG = {
    "base_url": "https://api.example.com/product",
    "app_key": "test_app_key",
    "auth_key": "test_auth_key",
    "field_names": "description,brand,upc_code",
    "language": "en",
}

TEST_BARCODES_DATA_CONFIG = {
    "base_url": "https://barcodes-data.p.rapidapi.com",
    "rapidapi_host": "barcodes-data.p.rapidapi.com",
    "rapidapi_key": "test_rapidapi_key",
}


class ProductAPIFactoryTest(TestCase):
    """Test the product API factory functions"""

    @override_settings(
        PRODUCT_API_PROVIDER="de_product",
        DE_PRODUCT_CONFIG=TEST_DE_PRODUCT_CONFIG,
    )
    def test_get_product_api_de_product(self):
        """Test getting DE Product API client"""
        api = get_product_api()
        self.assertIsInstance(api, DEProductAPI)

    @override_settings(
        PRODUCT_API_PROVIDER="barcodes_data",
        BARCODES_DATA_CONFIG=TEST_BARCODES_DATA_CONFIG,
    )
    def test_get_product_api_barcodes_data(self):
        """Test getting Barcodes Data API client"""
        api = get_product_api()
        self.assertIsInstance(api, BarcodesDataAPI)

    @override_settings(PRODUCT_API_PROVIDER="unsupported_provider")
    def test_get_product_api_unsupported_provider(self):
        """Test that unsupported provider raises ValueError"""
        with self.assertRaises(ValueError) as context:
            get_product_api()

        self.assertIn("Unsupported PRODUCT_API_PROVIDER", str(context.exception))
        self.assertIn("unsupported_provider", str(context.exception))

    def test_get_product_adapter_de_product(self):
        """Test getting DE Product adapter"""
        adapter = get_product_adapter("de_product")
        self.assertIsInstance(adapter, DEProductAdapter)

    def test_get_product_adapter_barcodes_data(self):
        """Test getting Barcodes Data adapter"""
        adapter = get_product_adapter("barcodes_data")
        self.assertIsInstance(adapter, BarcodesDataAdapter)

    @override_settings(PRODUCT_API_PROVIDER="de_product")
    def test_get_product_adapter_none_uses_default(self):
        """Test that None api_name uses the configured provider"""
        adapter = get_product_adapter(None)
        self.assertIsInstance(adapter, DEProductAdapter)

    @override_settings(PRODUCT_API_PROVIDER="barcodes_data")
    def test_get_product_adapter_none_uses_barcodes_data(self):
        """Test that None api_name uses barcodes_data when configured"""
        adapter = get_product_adapter(None)
        self.assertIsInstance(adapter, BarcodesDataAdapter)

    def test_get_product_adapter_unsupported_api(self):
        """Test that unsupported API name raises ValueError"""
        with self.assertRaises(ValueError) as context:
            get_product_adapter("unsupported_api")

        self.assertIn("Unsupported API name", str(context.exception))
        self.assertIn("unsupported_api", str(context.exception))

    @override_settings(
        PRODUCT_API_PROVIDER="de_product",
        DE_PRODUCT_CONFIG=TEST_DE_PRODUCT_CONFIG,
    )
    def test_get_current_api_and_adapter_de_product(self):
        """Test getting current API and adapter for DE Product"""
        api, adapter = get_current_api_and_adapter()
        self.assertIsInstance(api, DEProductAPI)
        self.assertIsInstance(adapter, DEProductAdapter)

    @override_settings(
        PRODUCT_API_PROVIDER="barcodes_data",
        BARCODES_DATA_CONFIG=TEST_BARCODES_DATA_CONFIG,
    )
    def test_get_current_api_and_adapter_barcodes_data(self):
        """Test getting current API and adapter for Barcodes Data"""
        api, adapter = get_current_api_and_adapter()
        self.assertIsInstance(api, BarcodesDataAPI)
        self.assertIsInstance(adapter, BarcodesDataAdapter)

    @override_settings(
        PRODUCT_API_PROVIDER="de_product",
        DE_PRODUCT_CONFIG=TEST_DE_PRODUCT_CONFIG,
    )
    def test_get_product_adapter_with_explicit_name_different_from_default(self):
        """Test that explicit api_name overrides default provider"""
        # Even though default is de_product, we can still get barcodes_data adapter
        adapter = get_product_adapter("barcodes_data")
        self.assertIsInstance(adapter, BarcodesDataAdapter)

    @override_settings(
        PRODUCT_API_PROVIDER="de_product",
        DE_PRODUCT_CONFIG=TEST_DE_PRODUCT_CONFIG,
    )
    def test_multiple_api_instances_are_separate(self):
        """Test that multiple calls create separate instances"""
        api1 = get_product_api()
        api2 = get_product_api()
        # They should be different instances
        self.assertIsNot(api1, api2)

    @override_settings(PRODUCT_API_PROVIDER="de_product")
    def test_multiple_adapter_instances_are_separate(self):
        """Test that multiple adapter calls create separate instances"""
        adapter1 = get_product_adapter()
        adapter2 = get_product_adapter()
        # They should be different instances
        self.assertIsNot(adapter1, adapter2)
