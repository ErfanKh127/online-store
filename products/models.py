from django.db import models
from django.conf import settings
from common.models import BaseModel

class Product(BaseModel):
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Optional: categories (simple version – you can later move to a separate Category model)
    category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name