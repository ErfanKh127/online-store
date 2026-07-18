from django.db import models
from django.conf import settings
from common.models import BaseModel

class Store(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stores')
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)

    def __str__(self):
        return self.name