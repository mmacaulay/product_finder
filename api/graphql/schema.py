import graphene
from api.models import Product
from api.graphql.types import ProductType
from api.services.de_product_api import DEProductAPI


class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    product_by_upc = graphene.Field(ProductType, upc=graphene.String(required=True))
    product_by_id = graphene.Field(ProductType, id=graphene.Int(required=True))

    def resolve_all_products(self, info):
        # Access authenticated user via info.context.user
        # user = info.context.user
        # if not user.is_authenticated:
        #     raise Exception('Authentication required')
        return Product.objects.all()

    def resolve_product_by_upc(self, info, upc):
        products = Product.objects.filter(upc_code=upc)
        if products.exists():
            return products.first()
        else:
            de_product_api = DEProductAPI()
            de_product = de_product_api.get_product(upc)
            if de_product:
                product = Product.objects.create(
                    upc_code=upc,
                    name=de_product["description"],
                    brand=de_product["brand"],
                    image_url=de_product.get("image"),
                    de_product_data=de_product,
                )
                product.save()
                return product
            else:
                return None

    def resolve_product_by_id(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None


schema = graphene.Schema(query=Query)
