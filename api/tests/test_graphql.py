from django.test import override_settings
from api.tests.base import FullMockedTestCase
from api.tests.fixtures import (
    create_mock_de_product_response,
    create_mock_de_product_empty_response,
    TEST_UPC_API_SUCCESS,
    TEST_UPC_API_EMPTY,
)
from graphene.test import Client
from api.graphql.schema import schema
from api.dao import ProductDAO
from unittest.mock import MagicMock
import responses


# Test configuration for DE Product API
TEST_DE_PRODUCT_CONFIG = {
    "base_url": "https://api.example.com/product",
    "app_key": "test_app_key",
    "auth_key": "test_auth_key",
    "field_names": "description,brand,upc_code",
    "language": "en",
}


@override_settings(DE_PRODUCT_CONFIG=TEST_DE_PRODUCT_CONFIG)
class GraphQLQueryTest(FullMockedTestCase):
    """Test GraphQL queries"""

    def setUp(self):
        """Create test products"""
        super().setUp()

        # Mock Firestore to return test products
        self.product1_data = {
            "id": "111111111111",
            "upc_code": "111111111111",
            "name": "Product One",
            "brand": "Brand A",
            "image_url": None,
            "created_at": None,
            "updated_at": None,
        }
        self.product2_data = {
            "id": "222222222222",
            "upc_code": "222222222222",
            "name": "Product Two",
            "brand": "Brand B",
            "image_url": None,
            "created_at": None,
            "updated_at": None,
        }

        # Configure mock to return products
        def mock_get_side_effect(upc):
            if upc == "111111111111":
                return self.product1_data
            elif upc == "222222222222":
                return self.product2_data
            return None

        # Mock ProductDAO methods
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.product1_data
        mock_doc.id = "111111111111"

        self.mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )
        self.mock_firestore.collection.return_value.limit.return_value.stream.return_value = [
            MagicMock(
                to_dict=lambda: self.product1_data,
                id="111111111111",
                exists=True,
            ),
            MagicMock(
                to_dict=lambda: self.product2_data,
                id="222222222222",
                exists=True,
            ),
        ]

        self.client = Client(schema)

    def test_query_all_products(self):
        """Test querying all products"""
        query = """
            query {
                allProducts {
                    upcCode
                    name
                    brand
                }
            }
        """
        result = self.client.execute(query)
        self.assertIsNone(result.get("errors"))
        products = result["data"]["allProducts"]
        self.assertEqual(len(products), 2)

    def test_query_product_by_upc(self):
        """Test querying a product by UPC code"""
        query = """
            query {
                productByUpc(upc: "111111111111") {
                    upcCode
                    name
                    brand
                }
            }
        """
        result = self.client.execute(query)
        self.assertIsNone(result.get("errors"))
        product = result["data"]["productByUpc"]
        self.assertEqual(product["upcCode"], "111111111111")
        self.assertEqual(product["name"], "Product One")

    def test_query_product_by_id(self):
        """Test querying a product by ID"""
        query = f"""
            query {{
                productById(id: "{self.product1_data['id']}") {{
                    id
                    upcCode
                    name
                }}
            }}
        """
        result = self.client.execute(query)
        self.assertIsNone(result.get("errors"))
        product = result["data"]["productById"]
        self.assertEqual(product["name"], "Product One")

    def test_query_nonexistent_upc(self):
        """Test querying with non-existent UPC returns None when API returns empty"""
        # Reset mock to return non-existent for this specific UPC
        mock_doc_not_exist = MagicMock()
        mock_doc_not_exist.exists = False
        self.mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc_not_exist
        )

        # Mock API to return empty response
        responses.add(
            responses.GET,
            "https://api.example.com/product",
            json=create_mock_de_product_empty_response(),
            status=200,
        )

        query = """
            query {
                productByUpc(upc: "999999999999") {
                    upcCode
                }
            }
        """
        result = self.client.execute(query)
        self.assertIsNone(result.get("errors"))
        self.assertIsNone(result["data"]["productByUpc"])

    def test_query_product_by_upc_with_api_call(self):
        """Test querying a product by UPC that triggers API call and creates product"""
        # Mock Firestore to return None first (product doesn't exist)
        mock_doc_not_exist = MagicMock()
        mock_doc_not_exist.exists = False

        # Then return the created product
        created_product = {
            "id": TEST_UPC_API_SUCCESS,
            "upc_code": TEST_UPC_API_SUCCESS,
            "name": "API Product",
            "brand": "API Brand",
            "image_url": None,
            "created_at": None,
            "updated_at": None,
        }
        mock_doc_created = MagicMock()
        mock_doc_created.exists = True
        mock_doc_created.to_dict.return_value = created_product
        mock_doc_created.id = TEST_UPC_API_SUCCESS

        # Setup side effects: first call returns not found, second returns created
        self.mock_firestore.collection.return_value.document.return_value.get.side_effect = [
            mock_doc_not_exist,  # First call in get_by_upc
            mock_doc_not_exist,  # Second call in create (checking exists)
            mock_doc_created,  # Third call after set()
        ]

        # Mock API response
        mock_response = create_mock_de_product_response(
            description="API Product", brand="API Brand", upc=TEST_UPC_API_SUCCESS
        )
        responses.add(
            responses.GET,
            "https://api.example.com/product",
            json=mock_response,
            status=200,
        )

        query = f"""
            query {{
                productByUpc(upc: "{TEST_UPC_API_SUCCESS}") {{
                    upcCode
                    name
                    brand
                }}
            }}
        """
        result = self.client.execute(query)
        self.assertIsNone(result.get("errors"))
        product = result["data"]["productByUpc"]
        self.assertEqual(product["upcCode"], TEST_UPC_API_SUCCESS)
        self.assertEqual(product["name"], "API Product")
        self.assertEqual(product["brand"], "API Brand")

        # Verify Firestore set was called to save the product
        self.mock_firestore.collection.return_value.document.return_value.set.assert_called_once()

    def test_query_product_by_upc_api_error(self):
        """Test querying a product when API returns an error"""
        # Reset mock to return non-existent for this UPC
        mock_doc_not_exist = MagicMock()
        mock_doc_not_exist.exists = False
        self.mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc_not_exist
        )

        # Mock API error response
        responses.add(
            responses.GET,
            "https://api.example.com/product",
            json={"error": "Internal Server Error"},
            status=500,
        )

        query = f"""
            query {{
                productByUpc(upc: "{TEST_UPC_API_EMPTY}") {{
                    upcCode
                }}
            }}
        """
        result = self.client.execute(query)
        # Should have an error in the response
        self.assertIsNotNone(result.get("errors"))

    def test_query_product_by_upc_api_empty_response(self):
        """Test querying a product when API returns empty results"""
        # Reset mock to return non-existent for this UPC
        mock_doc_not_exist = MagicMock()
        mock_doc_not_exist.exists = False
        self.mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc_not_exist
        )

        # Mock API empty response
        responses.add(
            responses.GET,
            "https://api.example.com/product",
            json=create_mock_de_product_empty_response(),
            status=200,
        )

        query = f"""
            query {{
                productByUpc(upc: "{TEST_UPC_API_EMPTY}") {{
                    upcCode
                }}
            }}
        """
        result = self.client.execute(query)
        self.assertIsNone(result.get("errors"))
        self.assertIsNone(result["data"]["productByUpc"])

    def test_query_product_with_image_url(self):
        """Test querying a product by UPC that includes image URL from API"""
        # Mock Firestore to return None first (product doesn't exist)
        mock_doc_not_exist = MagicMock()
        mock_doc_not_exist.exists = False

        # Then return the created product with image
        test_image_url = "https://example.com/test-product-image.jpg"
        created_product = {
            "id": "333333333333",
            "upc_code": "333333333333",
            "name": "Product with Image",
            "brand": "Image Brand",
            "image_url": test_image_url,
            "created_at": None,
            "updated_at": None,
        }
        mock_doc_created = MagicMock()
        mock_doc_created.exists = True
        mock_doc_created.to_dict.return_value = created_product
        mock_doc_created.id = "333333333333"

        self.mock_firestore.collection.return_value.document.return_value.get.side_effect = [
            mock_doc_not_exist,  # First call in get_by_upc
            mock_doc_not_exist,  # Second call in create (checking exists)
            mock_doc_created,  # Third call after set()
        ]

        # Mock API response with image
        mock_response = create_mock_de_product_response(
            description="Product with Image",
            brand="Image Brand",
            upc="333333333333",
            image=test_image_url,
        )
        responses.add(
            responses.GET,
            "https://api.example.com/product",
            json=mock_response,
            status=200,
        )

        query = """
            query {
                productByUpc(upc: "333333333333") {
                    upcCode
                    name
                    brand
                    imageUrl
                }
            }
        """
        result = self.client.execute(query)
        self.assertIsNone(result.get("errors"))
        product = result["data"]["productByUpc"]
        self.assertEqual(product["upcCode"], "333333333333")
        self.assertEqual(product["name"], "Product with Image")
        self.assertEqual(product["brand"], "Image Brand")
        self.assertEqual(product["imageUrl"], test_image_url)

        # Verify Firestore set was called with image URL
        call_args = (
            self.mock_firestore.collection.return_value.document.return_value.set.call_args
        )
        self.assertIn("image_url", call_args[0][0])
        self.assertEqual(call_args[0][0]["image_url"], test_image_url)
