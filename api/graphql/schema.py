import graphene
from api.dao import ProductDAO
from api.graphql.types import ProductType
from api.services.de_product_api import DEProductAPI


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

        if product:
            return product
        else:
            # Try to fetch from DE Product API
            de_product_api = DEProductAPI()
            de_product = de_product_api.get_product(upc)
            if de_product:
                # Create product in Firestore
                product = dao.create(
                    upc_code=upc,
                    name=de_product["description"],
                    brand=de_product["brand"],
                    image_url=de_product.get("image"),
                    de_product_data=de_product,
                )
                return product
            else:
                return None

    def resolve_product_by_id(self, info, id):
        # In Firestore, ID is the UPC code
        dao = ProductDAO()
        return dao.get_by_upc(id)


schema = graphene.Schema(query=Query)
