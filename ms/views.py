from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.http import JsonResponse
from difflib import SequenceMatcher
from .forms import CustomUserCreationForm, CategoryForm, TransactionForm, AccountForm
from .models import Category, Transaction, Account
import json
import logging


class SignUp(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


@login_required
def dashboard(request):
    current_user = request.user  # Это объект текущего пользователя
    return render(request, 'dashboard.html', {'user': current_user})


def home(request):
    return render(request, "ms/home/index.html")


def initial_page(request):
    return render(request, "ms/home/initial/initial.html")



@login_required
def categories_combined_view(request):
    user = request.user

    # Получаем категории пользователя
    categories = Category.objects.filter(user=user)

    # Разделение категорий на доходы и расходы
    income_categories = categories.filter(is_expense=False)
    expense_categories = categories.filter(is_expense=True)

    # Расчёт общей суммы значений для каждой группы
    total_income = sum(cat.value for cat in income_categories)
    total_expenses = sum(cat.value for cat in expense_categories)

    # Формирование данных для диаграмм
    def prepare_chart_data(categories, total_value):
        chart_data = []
        start_percentage = 0
        for category in categories:
            percentage = round((category.value / total_value * 100) if total_value > 0 else 0)
            end_percentage = start_percentage + percentage
            chart_data.append({
                'name': category.name,
                'percentage': percentage,
                'color': category.color,
                'start_percentage': start_percentage,
                'end_percentage': end_percentage,
            })
            start_percentage = end_percentage
        return chart_data

    income_data = prepare_chart_data(income_categories, total_income)
    expense_data = prepare_chart_data(expense_categories, total_expenses)

    # Передача данных в шаблон
    return render(request, 'ms/home/initial/categories/categories.html', {
        'income_categories': income_data,
        'expense_categories': expense_data,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'income_categorie': income_categories,  # Передаем оригинальные категории доходов
        'expense_categorie': expense_categories,  # Передаем оригинальные категории расходов
    })


# Проверка схожести имени категории
def is_name_similar(new_name, existing_names, threshold=0.8):
    for existing_name in existing_names:
        similarity = SequenceMatcher(None, new_name.lower(), existing_name.lower()).ratio()
        if similarity >= threshold:
            return True
    return False


# Обновленный метод для создания категории
@login_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            new_category_name = form.cleaned_data['name'].strip().lower()  # Нормализация имени

            # Проверяем существование категории с таким именем для текущего пользователя
            if Category.objects.filter(user=request.user, name__iexact=new_category_name).exists():
                return JsonResponse({"success": False, "error": "Категория с таким именем уже существует."})

            category = form.save(commit=False)
            category.user = request.user
            category.value = 0  # Устанавливаем значение value программно, например, на 0
            category.save()

            return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Ошибка при создании категории."})


@csrf_exempt
def update_category(request, category_name):
    if request.method == "POST":
        try:
            category = Category.objects.get(name=category_name, user=request.user)
            category.name = request.POST.get("name")
            category.color = request.POST.get("color")
            category.is_expense = request.POST.get("is_expense") == "on"
            category.value = category.value

            category.save()

            return JsonResponse({"success": True})
        except Category.DoesNotExist:
            return JsonResponse({"success": False, "error": "Категория не найдена."})


def get_category_data(request, category_name):
    try:
        category = Category.objects.get(name=category_name)
        return JsonResponse({
            'success': True,
            'category': {
                'name': category.name,
                'value': category.value,
                'color': category.color,
            }
        })
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)


@csrf_exempt
def delete_category(request, category_name):
    if request.method == 'DELETE':
        try:
            category = Category.objects.get(name=category_name)
            category.delete()
            return JsonResponse({'success': True})
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)


def transactions_view(request):
    transactions = Transaction.objects.all()
    return render(request, 'ms/home/initial/transaction/transaction.html', {'transactions': transactions})


@login_required
def create_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user

            # Получаем счет и категорию
            account = transaction.account
            category = transaction.category
            amount = transaction.amount

            # Обработка баланса счета
            if category.is_expense:  # Если категория расходная
                account.balance -= amount  # Уменьшаем баланс счета для расходов
                category.value += amount  # Добавляем сумму транзакции в категорию расходов
            else:  # Если категория доходная
                account.balance += amount  # Увеличиваем баланс счета для доходов
                category.value += amount  # Добавляем сумму транзакции в категорию доходов

            # Сохраняем изменения в счете и категории
            account.save()
            category.save()

            # Сохраняем транзакцию
            transaction.save()

            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = TransactionForm()
    return render(request, 'ms/home/initial/transaction/transaction_form_partial.html', {'form': form})


@login_required
def update_transaction(request, transaction_id):
    # Получаем текущую транзакцию для пользователя
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        # Получаем старые данные перед изменением
        old_amount = transaction.amount
        old_category = transaction.category

        # Создаем форму с новыми данными
        form = TransactionForm(request.POST, instance=transaction)

        if form.is_valid():
            # Сохраняем новые данные транзакции
            updated_transaction = form.save(commit=False)
            updated_transaction.user = request.user

            # Получаем счет и категорию
            account = updated_transaction.account
            category = updated_transaction.category
            new_amount = updated_transaction.amount

            # Рассчитываем разницу в суммах (для изменения баланса и категорий)
            amount_diff = new_amount - old_amount

            # Логирование для отладки
            print(f"Old amount: {old_amount}, New amount: {new_amount}, Difference: {amount_diff}")

            # Восстанавливаем старую сумму на счете и категории
            if old_category.is_expense:  # Для расходных категорий
                account.balance += old_amount  # Возвращаем старое значение расходов
            else:  # Для доходных категорий
                account.balance -= old_amount  # Возвращаем старое значение доходов

            # Обновляем категорию на основе разницы (если категория расходная или доходная)
            if category.is_expense:  # Для расходных категорий
                category.value -= amount_diff  # Уменьшаем или увеличиваем категорию расхода
            else:  # Для доходных категорий
                category.value += amount_diff  # Уменьшаем или увеличиваем категорию дохода

            # Обновляем баланс счета в зависимости от новой суммы транзакции
            if category.is_expense:  # Если категория расходная
                account.balance -= amount_diff  # Для расходных категорий уменьшаем баланс
            else:  # Если категория доходная
                account.balance += amount_diff  # Для доходных категорий увеличиваем баланс

            # Сохраняем изменения в счете и категории
            account.save()
            category.save()

            # Сохраняем обновленную транзакцию
            updated_transaction.save()

            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'ms/home/initial/transaction/transaction_form_partial.html', {'form': form})


@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'DELETE':
        transaction.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def accounts_view(request):
    accounts = Account.objects.filter(user=request.user)
    return render(request, 'ms/home/initial/accounts/account.html', {'accounts': accounts})


@login_required
def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = AccountForm()
    return render(request, 'ms/home/initial/accounts/account_form_partial.html', {'form': form})


@login_required
def update_account(request, account_id):
    account = get_object_or_404(Account, id=account_id, user=request.user)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = AccountForm(instance=account)
    return render(request, 'ms/home/initial/accounts/account_form_partial.html', {'form': form})


@login_required
def delete_account(request, account_id):
    account = get_object_or_404(Account, id=account_id, user=request.user)
    if request.method == 'DELETE':
        account.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


logger = logging.getLogger(__name__)


@login_required
def filter_transactions(request):
    filters = {}
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    year = request.GET.get('year')
    month = request.GET.get('month')

    if start_date and end_date:
        filters['transaction_date__range'] = (start_date, end_date)
    elif year and month:
        filters['transaction_date__year'] = year
        filters['transaction_date__month'] = month
    elif year:
        filters['transaction_date__year'] = year

    transactions = Transaction.objects.filter(user=request.user).filter(**filters)

    # Сериализация данных с учетом вложенных полей
    transactions_data = [
        {
            'id': tx.id,
            'amount': tx.amount,
            'transaction_date': tx.transaction_date,
            'description': tx.description,
            'category': {'id': tx.category.id, 'name': tx.category.name} if tx.category else None,
            'account': {
                'id': tx.account.id if tx.account else None,
                'name': tx.account.name if tx.account else 'Не указан',
                'currency': tx.account.currency_code if tx.account and hasattr(tx.account,
                                                                               'currency_code') else 'Не указана'
            } if tx.account else None,
        }
        for tx in transactions
    ]

    return JsonResponse({'success': True, 'transactions': transactions_data})


@login_required
def filter_categories(request):
    filters = {}
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    year = request.GET.get('year')
    month = request.GET.get('month')

    if start_date and end_date:
        filters['transaction_date__range'] = (start_date, end_date)
    elif year and month:
        filters['transaction_date__year'] = year
        filters['transaction_date__month'] = month
    elif year:
        filters['transaction_date__year'] = year

    # Получаем категории пользователя
    categories = Category.objects.filter(user=request.user)

    # Рассчитываем суммы транзакций по категориям и обновляем их данные
    category_data = []
    for category in categories:
        total = Transaction.objects.filter(
            category=category,
            user=request.user,
            **filters
        ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

        # Обновляем категории на сервере (пересчитываем значения или другие данные)
        category.value = float(total)
        category.save()

        category_data.append({
            'id': category.id,
            'name': category.name,
            'value': category.value,  # Значение уже обновлено на сервере
            'color': category.color,
        })

    return JsonResponse({'success': True, 'categories': category_data})


@csrf_exempt
def update_categories(request):
    if request.method == 'POST':
        try:
            # Парсим данные из запроса
            data = json.loads(request.body)
            categories = data.get('categories')

            if not categories:
                return JsonResponse({'success': False, 'error': 'No categories data provided'})

            # Обрабатываем и обновляем каждую категорию
            for category_data in categories:
                category_name = category_data.get('name')
                category_value = category_data.get('value')
                category_color = category_data.get('color')

                # Проверяем, что все необходимые данные переданы
                if not category_name or category_value is None or category_color is None:
                    return JsonResponse({'success': False, 'error': 'Missing data for category'})

                # Ищем категорию по имени и обновляем её
                category = Category.objects.filter(name=category_name).first()
                if category:
                    category.value = category_value
                    category.color = category_color
                    category.save()
                else:
                    return JsonResponse({'success': False, 'error': f'Category {category_name} not found'})

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
