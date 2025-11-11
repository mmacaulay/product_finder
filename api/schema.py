import graphene
from graphene_django import DjangoObjectType
from .models import DE_Product

class DE_ProductType(DjangoObjectType):
    class Meta:
        model = DE_Product
        fields = '__all__'

class Query(graphene.ObjectType):
    all_products = graphene.List(DE_ProductType)
    product_by_upc = graphene.Field(DE_ProductType, upc=graphene.String(required=True))
    product_by_id = graphene.Field(DE_ProductType, id=graphene.Int(required=True))

    def resolve_all_products(self, info):
        return DE_Product.objects.all()

    def resolve_product_by_upc(self, info, upc):
        try:
            return DE_Product.objects.get(upc_code=upc)
        except DE_Product.DoesNotExist:
            return None

    def resolve_product_by_id(self, info, id):
        try:
            return DE_Product.objects.get(id=id)
        except DE_Product.DoesNotExist:
            return None

schema = graphene.Schema(query=Query)