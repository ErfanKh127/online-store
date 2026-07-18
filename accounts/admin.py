from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_deleted')
    list_filter = ('role', 'is_deleted')
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('role', 'phone')}),
    )