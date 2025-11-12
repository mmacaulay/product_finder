from graphene_django import DjangoObjectType
from api.models import Product

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = (
          'id',
          'upc_code',
          'name',
          'brand',
          'created_at',
          'updated_at',
        )
