import graphene
from api.models import Product
from api.graphql.types import ProductType

class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    product_by_upc = graphene.Field(ProductType, upc=graphene.String(required=True))
    product_by_id = graphene.Field(ProductType, id=graphene.Int(required=True))

    def resolve_all_products(self, info):
        return Product.objects.all()

    def resolve_product_by_upc(self, info, upc):
        deproducts = Product.objects.filter(upc_code=upc)
        if deproducts.exists():
            return deproducts.first()
        else:
            return None

    def resolve_product_by_id(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None

schema = graphene.Schema(query=Query)