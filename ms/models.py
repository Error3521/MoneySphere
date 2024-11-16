from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings


from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=100)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# Модель категорий
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    color = models.CharField(max_length=7, default='#000000')  # HEX цвет
    is_expense = models.BooleanField(default=True)

    def __str__(self):
        return self.name



# Модель счетов
class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency_code = models.CharField(max_length=3)

    class Meta:
        unique_together = ('user', 'name')  # Уникальные счета для каждого пользователя

    def __str__(self):
        return f"{self.name} ({self.currency_code})"


# Модель транзакций
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateField()
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Transaction {self.id}: {self.amount} on {self.transaction_date}"

    @staticmethod
    def filter_by_year(user, year):
        return Transaction.objects.filter(user=user, transaction_date__year=year)

    @staticmethod
    def filter_by_month(user, year, month):
        return Transaction.objects.filter(user=user, transaction_date__year=year, transaction_date__month=month)

    @staticmethod
    def filter_by_range(user, start_date, end_date):
        return Transaction.objects.filter(user=user, transaction_date__range=(start_date, end_date))


