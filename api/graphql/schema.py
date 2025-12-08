import graphene
from api.dao import ProductDAO
from api.graphql.types import ProductType
from api.services.product_api_factory import get_current_api_and_adapter, get_product_adapter
from django.conf import settings


def _build_product_fields(adapted_data, current_provider, provider_data_field=None, raw_data=None):
    """
    Helper function to build product fields from adapted data.

    Args:
        adapted_data: The adapted product data from the adapter
        current_provider: The API provider name
        provider_data_field: Optional field name for storing raw provider data (e.g., "de_product_data")
        raw_data: Optional raw API response data

    Returns:
        Dictionary of fields to store in the database
    """
    fields = {
        "current_provider": current_provider,
        "name": adapted_data.get("name", ""),
        "brand": adapted_data.get("brand", ""),
        "image_url": adapted_data.get("image_url"),
        "description": adapted_data.get("description"),
        "category": adapted_data.get("category", []),
        "ingredients": adapted_data.get("ingredients"),
        "nutrition_facts": adapted_data.get("nutrition_facts"),
        "additional_data": adapted_data.get("additional_data", {}),
    }

    # Only add provider data field if both field name and raw data are provided
    if provider_data_field and raw_data is not None:
        fields[provider_data_field] = raw_data

    return fields


class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    product_by_upc = graphene.Field(ProductType, upc=graphene.String(required=True))
    product_by_id = graphene.Field(ProductType, id=graphene.String(required=True))

    def resolve_all_products(self, info):
        # Access authenticated user via info.context.firebase_user
        # user = info.context.firebase_user
        # if not user:
        #     raise Exception('Authentication required')
        dao = ProductDAO()
        return dao.get_all()

    def resolve_product_by_upc(self, info, upc):
        dao = ProductDAO()
        product = dao.get_by_upc(upc)
        current_provider = settings.PRODUCT_API_PROVIDER
        provider_data_field = f"{current_provider}_data"

        if product:
            # Product exists - check if we have data from current provider
            if not product.get(provider_data_field):
                # Need to fetch from current provider and add to existing product
                api, adapter = get_current_api_and_adapter()
                raw_product_data = api.get_product(upc)

                if raw_product_data:
                    # Adapt and update with raw data
                    adapted_data = adapter.adapt(raw_product_data)
                    update_fields = _build_product_fields(
                        adapted_data, current_provider, provider_data_field, raw_product_data
                    )

                    dao.update(upc, **update_fields)
                    product = dao.get_by_upc(upc)

            # If current_provider changed, update top-level fields from cached data
            elif product.get("current_provider") != current_provider:
                adapter = get_product_adapter(current_provider)
                raw_data = product.get(provider_data_field)
                adapted_data = adapter.adapt(raw_data)

                # Update top-level fields only (raw data already exists)
                update_fields = _build_product_fields(adapted_data, current_provider)

                dao.update(upc, **update_fields)
                product = dao.get_by_upc(upc)

            return product
        else:
            # Product doesn't exist - fetch from current provider
            api, adapter = get_current_api_and_adapter()
            raw_product_data = api.get_product(upc)

            if raw_product_data:
                adapted_data = adapter.adapt(raw_product_data)
                product_fields = _build_product_fields(
                    adapted_data, current_provider, provider_data_field, raw_product_data
                )

                product = dao.create(upc_code=upc, **product_fields)
                return product
            else:
                return None

    def resolve_product_by_id(self, info, id):
        # In Firestore, ID is the UPC code
        # This uses the same logic as product_by_upc
        return self.resolve_product_by_upc(info, id)


schema = graphene.Schema(query=Query)
