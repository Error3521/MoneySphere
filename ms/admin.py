from django.contrib import admin
from .models import User, Category, Account, Transaction

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Account)
admin.site.register(Transaction)
