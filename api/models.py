from django.db import models
from django.urls import reverse

class Product(models.Model):
    upc_code = models.CharField(max_length=12, null=False, unique=True)
    name = models.CharField(max_length=255, null=False)
    brand = models.CharField(max_length=255, null=False, blank=True)
    de_product_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])

# 1. description: The title (short description) of the item (up to 255 characters)
# 2. uom: Unit of measure: up to 128 characters that describe the item size or weight. Examples
# might be '24 ounces', '750 ml', '12 pieces', or even just "1".
# 3. brand: product brand
# 4. language: language of listing;
# 5. website: web site where more information can be found about this item (512 characters; the
# root of the product web page will be used if that is supplied and this field is empty.)
# 6. product web page: web page where more information can be found about this item (512
# characters);
# 7. image: location of the authoritative image of the item (512 characters);
# 8. thumbnail URL: location of a thumbnail image of the item (512 characters). Please note this
# is a extra charge feature, it is charged only if the requested thumbnail is available and
# supplied;
# 9. thumbnail width: location of an image of the item (512 characters);
# 10. thumbnail height: location of an image of the item (512 characters);
# 11. usage: romance description of the item, usage instructions if available (no length limit);
# 12. ingredients: elements from which the item is made (no length limit);
# 13. nutrition: if nutritional data if appropriate (no length limit);
# 14. categories: provide a list of product categories and tags that apply to this item in a commaseparated list (no length limit);
# 15. manufacturer name: manufacturer name
# 16. manufacturer address: manufacturer location: street address
# 17. manufacturer address 2: manufacturer location: suite, additional address
# 18. manufacturer city: manufacturer location: city;
# 19. manufacturer state: manufacturer location: state or political entity;
# 20. manufacturer postal code: manufacturer location: postal code
# 21. manufacturer country: manufacturer country
# 22. manufacturer phone: manufacturer phone
# 23. manufacturer contact: manufacturer email or contact name
# 24. GCP: Global Company Prefix
# 25. GCP Company: Company name of the CGP holder
# 26. GCP GLN: Global Location Number
# 27. GCP address 1: GCP holder's location: street address
# 28. GCP address 2: GCP holder's location: suite, additional address
# 29. GCP city: GCP holder's location: city;
# 30. GCP state: GCP holder's location: state or political entity;
# 31. GCP postal code: GCP holder's location: postal code
# 32. GCP country: GCP holder's country
# 33. GCP phone: GCP holder's phone
# 34. GCP contact: GCP holder's email or contact name
# 35. GCP phone: GCP holder's email or contact name
# 36. GCP fax: GCP holder's email or contact name
# 37. prices: an array of prices, including the currency, vendor business name, vendor address, and
# date the price data was collected;
# 38. system4: value 0 or 1; if 1 and a private/system 4 UPC number is provided. more than a
# single UPC record may be returned if the information is requested about a System 4 number.
# In V2, requests for information about System 4 numbers are ignored.