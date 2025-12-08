import responses
from django.test import override_settings
from api.tests.base import MockedAPITestCase
from api.tests.fixtures import (
    create_mock_barcodes_data_response,
    create_mock_barcodes_data_empty_response,
    TEST_UPC_API_SUCCESS,
)
from api.services.barcodes_data_api import BarcodesDataAPI


# Test configuration for Barcodes Data API
TEST_BARCODES_DATA_CONFIG = {
    "base_url": "https://barcodes-data.p.rapidapi.com",
    "rapidapi_host": "barcodes-data.p.rapidapi.com",
    "rapidapi_key": "test_rapidapi_key",
}


@override_settings(BARCODES_DATA_CONFIG=TEST_BARCODES_DATA_CONFIG)
class BarcodesDataAPITest(MockedAPITestCase):
    """Test the BarcodesDataAPI service"""

    def setUp(self):
        super().setUp()
        # Store test config values for reference in tests
        self.base_url = TEST_BARCODES_DATA_CONFIG["base_url"]
        self.rapidapi_host = TEST_BARCODES_DATA_CONFIG["rapidapi_host"]
        self.rapidapi_key = TEST_BARCODES_DATA_CONFIG["rapidapi_key"]

    def test_get_product_success(self):
        """Test successful product retrieval from API"""
        mock_response = create_mock_barcodes_data_response(
            title="Test Product", brand="Test Brand", upc=TEST_UPC_API_SUCCESS
        )

        responses.add(responses.GET, self.base_url, json=mock_response, status=200)

        api = BarcodesDataAPI()
        result = api.get_product(TEST_UPC_API_SUCCESS)

        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Test Product")
        self.assertEqual(result["brand"], "Test Brand")
        self.assertEqual(result["barcode_number"], TEST_UPC_API_SUCCESS)

    def test_get_product_empty_response(self):
        """Test API returns empty results"""
        responses.add(
            responses.GET,
            self.base_url,
            json=create_mock_barcodes_data_empty_response(),
            status=200,
        )

        api = BarcodesDataAPI()
        result = api.get_product(TEST_UPC_API_SUCCESS)

        self.assertIsNone(result)

    def test_get_product_error_status(self):
        """Test API returns error status code"""
        responses.add(
            responses.GET, self.base_url, json={"error": "Not Found"}, status=404
        )

        api = BarcodesDataAPI()
        with self.assertRaises(Exception) as context:
            api.get_product(TEST_UPC_API_SUCCESS)

        self.assertIn("Failed to get product", str(context.exception))
        self.assertIn("404", str(context.exception))

    def test_get_product_query_parameters(self):
        """Test that correct query parameters are sent to API"""
        mock_response = create_mock_barcodes_data_response()

        responses.add(responses.GET, self.base_url, json=mock_response, status=200)

        api = BarcodesDataAPI()
        api.get_product(TEST_UPC_API_SUCCESS)

        # Verify the request was made with correct parameters
        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[0].request
        self.assertIn("query", request.url)
        self.assertIn(TEST_UPC_API_SUCCESS, request.url)

    def test_get_product_headers(self):
        """Test that correct headers are sent to API"""
        mock_response = create_mock_barcodes_data_response()

        responses.add(responses.GET, self.base_url, json=mock_response, status=200)

        api = BarcodesDataAPI()
        api.get_product(TEST_UPC_API_SUCCESS)

        # Verify the request was made with correct headers
        request = responses.calls[0].request
        self.assertEqual(request.headers.get("x-rapidapi-host"), self.rapidapi_host)
        self.assertEqual(request.headers.get("x-rapidapi-key"), self.rapidapi_key)

    def test_init_missing_configuration(self):
        """Test that missing configuration values raise ValueError"""
        # Test missing base_url
        config = TEST_BARCODES_DATA_CONFIG.copy()
        config["base_url"] = ""
        with override_settings(BARCODES_DATA_CONFIG=config):
            with self.assertRaises(ValueError) as context:
                BarcodesDataAPI()
            self.assertIn("BARCODES_DATA_API_BASE_URL", str(context.exception))

        # Test missing rapidapi_host
        config = TEST_BARCODES_DATA_CONFIG.copy()
        config["rapidapi_host"] = ""
        with override_settings(BARCODES_DATA_CONFIG=config):
            with self.assertRaises(ValueError) as context:
                BarcodesDataAPI()
            self.assertIn("BARCODES_DATA_RAPIDAPI_HOST", str(context.exception))

        # Test missing rapidapi_key
        config = TEST_BARCODES_DATA_CONFIG.copy()
        config["rapidapi_key"] = ""
        with override_settings(BARCODES_DATA_CONFIG=config):
            with self.assertRaises(ValueError) as context:
                BarcodesDataAPI()
            self.assertIn("BARCODES_DATA_RAPIDAPI_KEY", str(context.exception))
