from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ProductAdapter(ABC):
    """
    Base adapter class for converting API-specific product data
    to a generic product data model.

    Each product API should have its own adapter that implements
    this interface.
    """

    @abstractmethod
    def adapt(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert API-specific raw data to generic product model.

        Args:
            raw_data: The raw response from the product API

        Returns:
            Dictionary with standardized product fields:
            {
                "name": str,              # Product name/title
                "brand": str,             # Brand or manufacturer
                "image_url": str,         # Primary product image URL
                "description": str,       # Product description
                "category": list[str],    # Product categories
                "ingredients": str,       # Ingredients list (if applicable)
                "nutrition_facts": dict,  # Nutrition information (if applicable)
                "additional_data": dict,  # Any other API-specific data
            }
        """
        pass

    @abstractmethod
    def get_api_name(self) -> str:
        """
        Return the name of the API this adapter is for.

        Returns:
            API identifier (e.g., 'de_product', 'barcodes_data')
        """
        pass
