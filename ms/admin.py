from django.contrib import admin

from .models import Currency
from .models import User, Category, Account, Transaction, Profile, Transfer

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Profile)
admin.site.register(Transfer)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'rate_to_base')
    search_fields = ('code', 'name')
