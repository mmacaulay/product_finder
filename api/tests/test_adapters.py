from django.test import TestCase
from api.adapters.de_product_adapter import DEProductAdapter
from api.adapters.barcodes_data_adapter import BarcodesDataAdapter


class DEProductAdapterTest(TestCase):
    """Test the DEProductAdapter"""

    def setUp(self):
        self.adapter = DEProductAdapter()

    def test_get_api_name(self):
        """Test that the adapter returns the correct API name"""
        self.assertEqual(self.adapter.get_api_name(), "de_product")

    def test_adapt_complete_data(self):
        """Test adapting a complete DE Product API response"""
        raw_data = {
            "description": "Test Product",
            "brand": "Test Brand",
            "image": "https://example.com/image.jpg",
            "categories": ["Food", "Snacks"],
            "ingredients": "Test ingredients",
            "formattedNutrition": "Test nutrition",
            "uom": "1 unit",
            "usage": "Test usage",
            "language": "en",
            "website": "https://example.com",
            "product_web_page": "https://example.com/product",
            "manufacturer": "Test Manufacturer",
            "thumbnail": "https://example.com/thumb.jpg",
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["name"], "Test Product")
        self.assertEqual(result["brand"], "Test Brand")
        self.assertEqual(result["image_url"], "https://example.com/image.jpg")
        self.assertEqual(result["description"], "Test Product")
        self.assertEqual(result["category"], ["Food", "Snacks"])
        self.assertEqual(result["ingredients"], "Test ingredients")
        self.assertEqual(result["nutrition_facts"], "Test nutrition")
        self.assertEqual(result["additional_data"]["uom"], "1 unit")
        self.assertEqual(result["additional_data"]["manufacturer"], "Test Manufacturer")

    def test_adapt_minimal_data(self):
        """Test adapting minimal DE Product API response"""
        raw_data = {}

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["name"], "")
        self.assertEqual(result["brand"], "")
        self.assertIsNone(result["image_url"])
        self.assertEqual(result["description"], "")
        self.assertEqual(result["category"], [])
        self.assertIsNone(result["ingredients"])
        self.assertIsNone(result["nutrition_facts"])
        self.assertIsNotNone(result["additional_data"])

    def test_adapt_nutrition_fallback(self):
        """Test that nutrition_facts falls back to 'nutrition' field if 'formattedNutrition' is missing"""
        raw_data = {
            "nutrition": "Raw nutrition data",
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["nutrition_facts"], "Raw nutrition data")

    def test_adapt_formatted_nutrition_takes_precedence(self):
        """Test that formattedNutrition takes precedence over nutrition"""
        raw_data = {
            "formattedNutrition": "Formatted nutrition",
            "nutrition": "Raw nutrition",
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["nutrition_facts"], "Formatted nutrition")

    def test_adapt_missing_optional_fields(self):
        """Test that missing optional fields are handled gracefully"""
        raw_data = {
            "description": "Test Product",
            "brand": "Test Brand",
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["name"], "Test Product")
        self.assertEqual(result["brand"], "Test Brand")
        self.assertIsNone(result["image_url"])
        self.assertEqual(result["category"], [])


class BarcodesDataAdapterTest(TestCase):
    """Test the BarcodesDataAdapter"""

    def setUp(self):
        self.adapter = BarcodesDataAdapter()

    def test_get_api_name(self):
        """Test that the adapter returns the correct API name"""
        self.assertEqual(self.adapter.get_api_name(), "barcodes_data")

    def test_adapt_complete_data(self):
        """Test adapting a complete Barcodes Data API response"""
        raw_data = {
            "title": "Test Product",
            "brand": "Test Brand",
            "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            "description": "Test description",
            "category": "Food > Snacks",
            "ingredients": "Test ingredients",
            "nutrition_facts": "Test nutrition",
            "manufacturer": "Test Manufacturer",
            "artist": "Test Artist",
            "author": "Test Author",
            "attributes": ["attr1", "attr2"],
            "barcode_formats": {"UPC": "123456789012"},
            "features": ["feature1", "feature2"],
            "online_stores": ["store1", "store2"],
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["name"], "Test Product")
        self.assertEqual(result["brand"], "Test Brand")
        self.assertEqual(result["image_url"], "https://example.com/image1.jpg")
        self.assertEqual(result["description"], "Test description")
        self.assertEqual(result["category"], "Food > Snacks")
        self.assertEqual(result["ingredients"], "Test ingredients")
        self.assertEqual(result["nutrition_facts"], "Test nutrition")
        self.assertEqual(result["additional_data"]["manufacturer"], "Test Manufacturer")
        self.assertEqual(result["additional_data"]["artist"], "Test Artist")

    def test_adapt_minimal_data(self):
        """Test adapting minimal Barcodes Data API response"""
        raw_data = {}

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["name"], "")
        self.assertEqual(result["brand"], "")
        self.assertIsNone(result["image_url"])
        self.assertEqual(result["description"], "")
        self.assertEqual(result["category"], [])
        self.assertIsNone(result["ingredients"])
        self.assertIsNone(result["nutrition_facts"])
        self.assertIsNotNone(result["additional_data"])

    def test_adapt_image_from_array(self):
        """Test that first image is extracted from images array"""
        raw_data = {
            "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["image_url"], "https://example.com/image1.jpg")

    def test_adapt_empty_images_array(self):
        """Test handling of empty images array"""
        raw_data = {
            "images": [],
        }

        result = self.adapter.adapt(raw_data)

        self.assertIsNone(result["image_url"])

    def test_adapt_no_images_field(self):
        """Test handling when images field is missing"""
        raw_data = {}

        result = self.adapter.adapt(raw_data)

        self.assertIsNone(result["image_url"])

    def test_adapt_brand_fallback_to_manufacturer(self):
        """Test that brand falls back to manufacturer if not provided"""
        raw_data = {
            "manufacturer": "Test Manufacturer",
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["brand"], "Test Manufacturer")

    def test_adapt_brand_takes_precedence(self):
        """Test that brand takes precedence over manufacturer"""
        raw_data = {
            "brand": "Test Brand",
            "manufacturer": "Test Manufacturer",
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["brand"], "Test Brand")

    def test_adapt_empty_brand_uses_manufacturer(self):
        """Test that empty brand string falls back to manufacturer"""
        raw_data = {
            "brand": "",
            "manufacturer": "Test Manufacturer",
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["brand"], "Test Manufacturer")

    def test_adapt_missing_optional_fields(self):
        """Test that missing optional fields are handled gracefully"""
        raw_data = {
            "title": "Test Product",
            "brand": "Test Brand",
        }

        result = self.adapter.adapt(raw_data)

        self.assertEqual(result["name"], "Test Product")
        self.assertEqual(result["brand"], "Test Brand")
        self.assertIsNone(result["image_url"])
        self.assertEqual(result["category"], [])
