"""
Factory for creating product API clients and adapters.

This module provides a centralized way to get the appropriate
product API client and adapter based on configuration.
"""

from django.conf import settings
from api.services.de_product_api import DEProductAPI
from api.services.barcodes_data_api import BarcodesDataAPI
from api.adapters.de_product_adapter import DEProductAdapter
from api.adapters.barcodes_data_adapter import BarcodesDataAdapter


def get_product_api():
    """
    Get the configured product API client.

    Returns:
        Instance of the configured product API client (DEProductAPI or BarcodesDataAPI)

    Raises:
        ValueError: If the configured provider is not supported
    """
    provider = settings.PRODUCT_API_PROVIDER

    if provider == "de_product":
        return DEProductAPI()
    elif provider == "barcodes_data":
        return BarcodesDataAPI()
    else:
        raise ValueError(
            f"Unsupported PRODUCT_API_PROVIDER: {provider}. "
            "Supported values: 'de_product', 'barcodes_data'"
        )


def get_product_adapter(api_name=None):
    """
    Get the product adapter for the specified API.

    Args:
        api_name: The API name (e.g., 'de_product', 'barcodes_data').
                  If None, uses the configured PRODUCT_API_PROVIDER.

    Returns:
        Instance of the appropriate ProductAdapter

    Raises:
        ValueError: If the API name is not supported
    """
    if api_name is None:
        api_name = settings.PRODUCT_API_PROVIDER

    if api_name == "de_product":
        return DEProductAdapter()
    elif api_name == "barcodes_data":
        return BarcodesDataAdapter()
    else:
        raise ValueError(
            f"Unsupported API name: {api_name}. "
            "Supported values: 'de_product', 'barcodes_data'"
        )


def get_current_api_and_adapter():
    """
    Get both the current API client and its adapter.

    Returns:
        Tuple of (api_client, adapter)
    """
    api = get_product_api()
    adapter = get_product_adapter()
    return api, adapter
