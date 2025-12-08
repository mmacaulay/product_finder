from typing import Dict, Any
from .base_adapter import ProductAdapter


class BarcodesDataAdapter(ProductAdapter):
    """
    Adapter for Barcodes Data API (RapidAPI) responses.

    Converts Barcodes Data API data to the generic product model.
    """

    def adapt(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Barcodes Data API response to generic product model.

        Args:
            raw_data: Raw response from Barcodes Data API (the "product" object)

        Returns:
            Standardized product data dictionary
        """
        # Extract the first image from the images array, if available
        images = raw_data.get("images", [])
        image_url = images[0] if images else None

        # Use brand if available, otherwise fall back to manufacturer
        brand = raw_data.get("brand") or raw_data.get("manufacturer", "")

        return {
            "name": raw_data.get("title", ""),
            "brand": brand,
            "image_url": image_url,
            "description": raw_data.get("description", ""),
            "category": raw_data.get("category", []),
            "ingredients": raw_data.get("ingredients"),
            "nutrition_facts": raw_data.get("nutrition_facts"),
            "additional_data": {
                "artist": raw_data.get("artist"),
                "author": raw_data.get("author"),
                "attributes": raw_data.get("attributes", []),
                "barcode_formats": raw_data.get("barcode_formats", {}),
                "features": raw_data.get("features", []),
                "manufacturer": raw_data.get("manufacturer"),
                "online_stores": raw_data.get("online_stores", []),
            },
        }

    def get_api_name(self) -> str:
        """Return the API identifier."""
        return "barcodes_data"
