from django.db import models
from django.urls import reverse

class Product(models.Model):
    upc_code = models.CharField(max_length=12, null=False, unique=True)
    name = models.CharField(max_length=255, null=False)
    brand = models.CharField(max_length=255, null=True, blank=True)
    de_product_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])