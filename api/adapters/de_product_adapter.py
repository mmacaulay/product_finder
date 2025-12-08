from typing import Dict, Any
from .base_adapter import ProductAdapter


class DEProductAdapter(ProductAdapter):
    """
    Adapter for DE Product API responses.

    Converts DE Product API data to the generic product model.
    """

    def adapt(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert DE Product API response to generic product model.

        Args:
            raw_data: Raw response from DE Product API

        Returns:
            Standardized product data dictionary
        """
        return {
            "name": raw_data.get("description", ""),
            "brand": raw_data.get("brand", ""),
            "image_url": raw_data.get("image"),
            "description": raw_data.get("description", ""),
            "category": raw_data.get("categories", []),
            "ingredients": raw_data.get("ingredients"),
            "nutrition_facts": raw_data.get("formattedNutrition")
            or raw_data.get("nutrition"),
            "additional_data": {
                "uom": raw_data.get("uom"),
                "usage": raw_data.get("usage"),
                "language": raw_data.get("language"),
                "website": raw_data.get("website"),
                "product_web_page": raw_data.get("product_web_page"),
                "manufacturer": raw_data.get("manufacturer"),
                "thumbnail": raw_data.get("thumbnail"),
            },
        }

    def get_api_name(self) -> str:
        """Return the API identifier."""
        return "de_product"
