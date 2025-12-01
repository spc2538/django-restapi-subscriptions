from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

@admin.register(Account)
class AccountAdmin(UserAdmin):
    model = Account
    list_display = ('email', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email',)
