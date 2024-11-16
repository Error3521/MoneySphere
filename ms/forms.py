from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from .models import Category, Account, Transaction
from django import forms


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'account', 'amount', 'transaction_date', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'transaction_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }



class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email',)

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'value', 'color', 'is_expense']  # Добавляем поле is_expense
        widgets = {
            'is_expense': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_expense': 'Это расход?',
        }

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance', 'currency_code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
