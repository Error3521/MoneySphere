from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Category, Account, Transaction
from .models import User


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
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )

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
        fields = ['name', 'color', 'is_expense']
        widgets = {
            'is_expense': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
        }
        labels = {
            'is_expense': 'Это расход?',
            'color': 'Цвет категории',
            'name': 'Название категории',
        }

    def __init__(self, *args, **kwargs):
        # Передаем пользователя при создании формы
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip().lower()
        # Проверяем уникальность имени для конкретного пользователя
        if Category.objects.filter(user=self.user, name__iexact=name).exists():
            raise ValidationError("Категория с таким именем уже существует.")
        return name


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance', 'currency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),  # Выпадающий список
        }
