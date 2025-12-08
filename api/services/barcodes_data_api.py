import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class BarcodesDataAPI:
    """
    Service for interacting with the Barcodes Data API (RapidAPI).

    Configuration is managed through Django settings (BARCODES_DATA_CONFIG).
    """

    def __init__(self):
        """
        Initialize the Barcodes Data API client.

        Raises:
            ValueError: If required configuration is missing
        """
        config = settings.BARCODES_DATA_CONFIG

        self.base_url = config.get("base_url")
        self.rapidapi_host = config.get("rapidapi_host")
        self.rapidapi_key = config.get("rapidapi_key")

        # Validate required configuration
        if not self.base_url:
            raise ValueError(
                "BARCODES_DATA_API_BASE_URL is required. "
                "Set it in your environment or Django settings."
            )
        if not self.rapidapi_host:
            raise ValueError(
                "BARCODES_DATA_RAPIDAPI_HOST is required. "
                "Set it in your environment or Django settings."
            )
        if not self.rapidapi_key:
            raise ValueError(
                "BARCODES_DATA_RAPIDAPI_KEY is required. "
                "Set it in your environment or Django settings."
            )

        logger.info(f"BarcodesDataAPI initialized with base_url: {self.base_url}")

    def get_product(self, upc_code):
        """
        Fetch product data by UPC code.

        Returns the raw API response - use BarcodesDataAdapter to convert
        to the generic product model.

        Args:
            upc_code: The UPC code to look up

        Returns:
            Raw product data from the API's "product" field, or None if not found

        Raises:
            Exception: If the API request fails
        """
        query_params = {
            "query": upc_code,
        }

        headers = {
            "x-rapidapi-host": self.rapidapi_host,
            "x-rapidapi-key": self.rapidapi_key,
        }

        logger.debug(f"Querying Barcodes Data API with UPC: {upc_code}")
        response = requests.get(self.base_url, params=query_params, headers=headers)

        if response.status_code != 200:
            raise Exception(
                f"Failed to get product: {response.status_code} {response.text}"
            )

        result = response.json()
        logger.debug(f"API Response: {result}")

        # Return the raw "product" object from the API response
        # The adapter will convert this to our generic product model
        return result.get("product")
