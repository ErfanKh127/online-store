from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'price', 'stock', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('store', 'is_active')
    search_fields = ('name', 'description')