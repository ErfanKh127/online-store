from django.contrib.auth.models import AbstractUser
from django.db import models
from common.models import BaseModel

class User(AbstractUser, BaseModel):
    """
    Custom User model with roles.
    Extends AbstractUser and BaseModel (soft delete, timestamps).
    """
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        SELLER = 'seller', 'Seller'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    
    # Optional: add extra fields like phone number
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username