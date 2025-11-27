import responses
from django.test import override_settings
from api.tests.base import MockedAPITestCase
from api.tests.fixtures import (
    create_mock_de_product_response,
    create_mock_de_product_empty_response,
    TEST_UPC_API_SUCCESS,
)
from api.services.de_product_api import DEProductAPI


# Test configuration for DE Product API
TEST_DE_PRODUCT_CONFIG = {
    "base_url": "https://api.example.com/product",
    "app_key": "test_app_key",
    "auth_key": "test_auth_key",
    "field_names": "description,brand,upc_code",
    "language": "en",
}


@override_settings(DE_PRODUCT_CONFIG=TEST_DE_PRODUCT_CONFIG)
class DEProductAPITest(MockedAPITestCase):
    """Test the DEProductAPI service"""

    def setUp(self):
        super().setUp()
        # Store test config values for reference in tests
        self.base_url = TEST_DE_PRODUCT_CONFIG["base_url"]
        self.app_key = TEST_DE_PRODUCT_CONFIG["app_key"]
        self.auth_key = TEST_DE_PRODUCT_CONFIG["auth_key"]
        self.field_names = TEST_DE_PRODUCT_CONFIG["field_names"]

    def test_get_product_success(self):
        """Test successful product retrieval from API"""
        mock_response = create_mock_de_product_response(
            description="Test Product", brand="Test Brand", upc=TEST_UPC_API_SUCCESS
        )

        responses.add(responses.GET, self.base_url, json=mock_response, status=200)

        api = DEProductAPI()
        result = api.get_product(TEST_UPC_API_SUCCESS)

        self.assertIsNotNone(result)
        self.assertEqual(result["description"], "Test Product")
        self.assertEqual(result["brand"], "Test Brand")
        self.assertEqual(result["upc_code"], TEST_UPC_API_SUCCESS)

    def test_get_product_empty_response(self):
        """Test API returns empty results"""
        responses.add(
            responses.GET,
            self.base_url,
            json=create_mock_de_product_empty_response(),
            status=200,
        )

        api = DEProductAPI()
        result = api.get_product(TEST_UPC_API_SUCCESS)

        self.assertIsNone(result)

    def test_get_product_error_status(self):
        """Test API returns error status code"""
        responses.add(
            responses.GET, self.base_url, json={"error": "Not Found"}, status=404
        )

        api = DEProductAPI()
        with self.assertRaises(Exception) as context:
            api.get_product(TEST_UPC_API_SUCCESS)

        self.assertIn("Failed to get product", str(context.exception))
        self.assertIn("404", str(context.exception))

    def test_get_product_query_parameters(self):
        """Test that correct query parameters are sent to API"""
        mock_response = create_mock_de_product_response()

        responses.add(responses.GET, self.base_url, json=mock_response, status=200)

        api = DEProductAPI()
        api.get_product(TEST_UPC_API_SUCCESS)

        # Verify the request was made with correct parameters
        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[0].request
        self.assertIn("upc_code", request.url)
        self.assertIn("app_key", request.url)
        self.assertIn("signature", request.url)
        self.assertIn("language", request.url)
        self.assertIn("field_names", request.url)

    def test_make_auth_token(self):
        """Test authentication token generation"""
        api = DEProductAPI()
        token = api.make_auth_token("test_upc")

        # Token should be a base64 encoded string
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

        # Same input should produce same token
        token2 = api.make_auth_token("test_upc")
        self.assertEqual(token, token2)

        # Different input should produce different token
        token3 = api.make_auth_token("different_upc")
        self.assertNotEqual(token, token3)

    def test_init_missing_configuration(self):
        """Test that missing configuration values raise ValueError"""
        # Test missing base_url
        config = TEST_DE_PRODUCT_CONFIG.copy()
        config["base_url"] = ""
        with override_settings(DE_PRODUCT_CONFIG=config):
            with self.assertRaises(ValueError) as context:
                DEProductAPI()
            self.assertIn("DE_PRODUCT_API_BASE_URL", str(context.exception))

        # Test missing app_key
        config = TEST_DE_PRODUCT_CONFIG.copy()
        config["app_key"] = ""
        with override_settings(DE_PRODUCT_CONFIG=config):
            with self.assertRaises(ValueError) as context:
                DEProductAPI()
            self.assertIn("DE_PRODUCT_APP_KEY", str(context.exception))

        # Test missing auth_key
        config = TEST_DE_PRODUCT_CONFIG.copy()
        config["auth_key"] = ""
        with override_settings(DE_PRODUCT_CONFIG=config):
            with self.assertRaises(ValueError) as context:
                DEProductAPI()
            self.assertIn("DE_PRODUCT_AUTH_KEY", str(context.exception))

        # Test missing field_names
        config = TEST_DE_PRODUCT_CONFIG.copy()
        config["field_names"] = ""
        with override_settings(DE_PRODUCT_CONFIG=config):
            with self.assertRaises(ValueError) as context:
                DEProductAPI()
            self.assertIn("DE_PRODUCT_FIELD_NAMES", str(context.exception))
