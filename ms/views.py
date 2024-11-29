import json
import logging
from collections import defaultdict
from decimal import Decimal
from difflib import SequenceMatcher

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import CreateView

from .forms import CustomUserCreationForm, CategoryForm, TransactionForm, AccountForm
from .models import Category, Transaction, Currency, Account, Transfer, User, Profile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class SignUp(CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def form_invalid(self, form):
        # Лог ошибок для отладки
        for field, errors in form.errors.items():
            print(f"Поле {field}: {', '.join(errors)}")
        return super().form_invalid(form)


@login_required
def dashboard(request):
    current_user = request.user  # Это объект текущего пользователя
    return render(request, 'dashboard.html', {'user': current_user})


def home(request):
    return render(request, "ms/home/index.html")


def initial_page(request):
    return render(request, "ms/home/initial/initial.html")


def is_name_similar(new_name, existing_names, threshold=0.8):
    for existing_name in existing_names:
        similarity = SequenceMatcher(None, new_name.lower(), existing_name.lower()).ratio()
        if similarity >= threshold:
            return True
    return False


@login_required
def categories_combined_view(request):
    user = request.user
    target_currency = user.profile.default_currency  # Валюта профиля
    if target_currency is None:
        from ms.models import Currency  # Импортируйте модель валют, если нужно
        target_currency = Currency.objects.get_or_create(code="RUB")[0]
    categories = Category.objects.filter(user=user)
    transactions = Transaction.objects.filter(user=user)

    # Инициализация словаря category_totals
    category_totals = defaultdict(lambda: {'value': 0, 'transactions': []})
    # Разделение категорий на доходы и расходы
    income_categories = categories.filter(is_expense=False)
    expense_categories = categories.filter(is_expense=True)

    # Расчёт общей суммы значений для каждой группы
    total_income = sum(cat.value for cat in income_categories)
    total_expenses = sum(cat.value for cat in expense_categories)

    def prepare_chart_data(categories, total_value):
        chart_data = []
        start_percentage = 0
        for category in categories:
            percentage = round((category['value'] / total_value * 100) if total_value > 0 else 0)
            end_percentage = start_percentage + percentage
            chart_data.append({
                'name': category['name'],
                'value': category['value'],
                'percentage': percentage,
                'color': category['color'],
                'start_percentage': start_percentage,
                'end_percentage': end_percentage,
            })
            start_percentage = end_percentage
        return chart_data

    # Обработка транзакций
    for transaction in transactions:
        category = transaction.category
        amount_in_target_currency = transaction.get_amount_in_currency(target_currency)
        category_totals[category]['value'] += amount_in_target_currency
        category_totals[category]['transactions'].append(transaction)

    # Убедимся, что все категории учтены
    for category in categories:
        if category not in category_totals:
            category_totals[category] = {'value': 0, 'transactions': []}

    # Подготовка данных для шаблона
    income_categories = []
    expense_categories = []
    total_income = 0
    total_expenses = 0

    for category, data in category_totals.items():
        if category.is_expense:
            total_expenses += data['value']
            expense_categories.append({
                'id': category.id,
                'name': category.name,
                'value': round(data['value'], 2),
                'color': category.color,
            })
        else:
            total_income += data['value']
            income_categories.append({
                'id': category.id,
                'name': category.name,
                'value': round(data['value'], 2),
                'color': category.color,
            })

    income_data = prepare_chart_data(income_categories, total_income)
    expense_data = prepare_chart_data(expense_categories, total_expenses)

    # Передача данных в шаблон
    return render(request, 'ms/home/initial/categories/categories.html', {
        'income_categorie': income_categories,
        'expense_categorie': expense_categories,
        'total_income': round(total_income, 2),
        'total_expenses': round(total_expenses, 2),
        'income_categories': income_data,
        'expense_categories': expense_data,
        'currency_code': target_currency.code,
    })


@login_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']

            # Проверяем существование категории с таким именем у текущего пользователя
            if Category.objects.filter(user=request.user, name=name).exists():
                return JsonResponse({
                    "success": False,
                    "error": "Категория с таким именем уже существует у вас."
                }, status=400)

            try:
                category = form.save(commit=False)
                category.user = request.user
                category.value = 0  # Устанавливаем значение value программно
                category.save()

                return JsonResponse({"success": True})

            except IntegrityError:
                return JsonResponse({
                    "success": False,
                    "error": "Ошибка при сохранении категории."
                }, status=500)

    return JsonResponse({"success": False, "error": "Ошибка при создании категории."}, status=400)


@csrf_exempt
def update_category(request, category_id):
    if request.method == "POST":
        try:
            category = Category.objects.get(id=category_id, user=request.user)
            new_name = request.POST.get("name").strip().lower()

            # Проверяем наличие категории с таким же именем у пользователя
            if Category.objects.filter(user=request.user, name__iexact=new_name).exclude(id=category_id).exists():
                return JsonResponse({"success": False, "error": "Категория с таким именем уже существует."})

            category.name = new_name
            category.color = request.POST.get("color")

            # Преобразуем строку в булев тип
            is_expense = request.POST.get("is_expense") == "True"
            category.is_expense = is_expense

            category.save()

            return JsonResponse({"success": True})
        except Category.DoesNotExist:
            return JsonResponse({"success": False, "error": "Категория не найдена."})


def get_category_data(request, category_id):
    try:
        category = Category.objects.get(id=category_id, user=request.user)
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'value': category.value,
                'color': category.color,
                'is_expense': category.is_expense,
            }
        })
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)


@csrf_exempt
def delete_category(request, category_id):
    if request.method == 'DELETE':
        try:
            category = Category.objects.get(id=category_id)
            category.delete()
            return JsonResponse({'success': True})
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Категория не найдена'}, status=404)


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


@login_required
def update_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            # Сохраняем старые значения
            old_account = transaction.account
            old_category = transaction.category
            old_amount = transaction.amount

            # Получаем новые значения из формы
            updated_transaction = form.save(commit=False)
            new_account = updated_transaction.account
            new_category = updated_transaction.category
            new_amount = updated_transaction.amount

            # Обработка старых данных для счёта и категории
            if old_category.is_expense:
                old_account.balance += old_amount  # Возвращаем старое значение к счету
                old_category.value -= old_amount  # Уменьшаем значение категории
            else:
                old_account.balance -= old_amount  # Убираем старое значение из счёта
                old_category.value -= old_amount  # Уменьшаем значение категории

            # Сохранение старых данных
            old_account.save()
            old_category.save()

            # Применение новых данных
            if new_category.is_expense:
                new_account.balance += old_amount  # Добавляем старое значение транзакции
                new_account.balance -= new_amount  # Вычитаем новое значение транзакции
                new_category.value += new_amount  # Увеличиваем значение категории
            else:
                new_account.balance -= old_amount  # Убираем старое значение транзакции
                new_account.balance += new_amount  # Добавляем новое значение транзакции
                new_category.value += new_amount  # Увеличиваем значение категории

            # Сохранение новых данных
            new_account.save()
            new_category.save()

            # Сохранение обновлённой транзакции
            updated_transaction.save()

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        # Для отображения формы редактирования
        accounts = Account.objects.filter(user=request.user)
        categories = Category.objects.filter(user=request.user)
        form = TransactionForm(instance=transaction)
        form.fields['account'].queryset = accounts
        form.fields['category'].queryset = categories
        return render(request, 'ms/home/initial/transaction/transaction_form_partial.html', {'form': form})


@login_required
def transactions_view(request):
    accounts = Account.objects.filter(user=request.user)  # Получение счетов
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'ms/home/initial/transaction/transaction.html', {
        'transactions': transactions,
        'accounts': accounts,  # Добавляем счета в контекст
    })


@login_required
def create_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user

            account = transaction.account
            category = transaction.category
            amount = transaction.amount

            if category.is_expense:
                account.balance -= amount
                category.value += amount
            else:
                account.balance += amount
                category.value += amount

            account.save()
            category.save()

            transaction.save()

            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    else:
        # Отфильтруем категории и счета для текущего пользователя
        accounts = Account.objects.filter(user=request.user)
        categories = Category.objects.filter(user=request.user)
        form = TransactionForm()
        form.fields['account'].queryset = accounts
        form.fields['category'].queryset = categories
    return render(request, 'ms/home/initial/transaction/transaction_form_partial.html', {'form': form})


def process_transaction_change(old_transaction=None, new_transaction=None):
    try:
        account_balance = None
        category_value = None

        # Шаг 1: Откат старой транзакции
        if old_transaction:
            account_balance = old_transaction.account.balance
            category_value = old_transaction.category.value
            amount = old_transaction.amount

            if old_transaction.category.is_expense:
                account_balance += amount
                category_value -= amount
            else:
                account_balance -= amount
                category_value -= amount

            logging.info(
                f"Откат старой транзакции: account_balance={account_balance}, category_value={category_value}, "
                f"amount={amount}"
            )

        # Шаг 2: Применение новой транзакции
        if new_transaction:
            if account_balance is None:
                account_balance = new_transaction.account.balance
            if category_value is None:
                category_value = new_transaction.category.value
            amount = new_transaction.amount

            if new_transaction.category.is_expense:
                account_balance -= amount
                category_value += amount
            else:
                account_balance += amount
                category_value += amount

            logging.info(
                f"Применение новой транзакции: account_balance={account_balance}, category_value={category_value}, "
                f"amount={amount}"
            )

        # Шаг 3: Обновление балансов
        if old_transaction or new_transaction:
            if old_transaction:
                old_transaction.account.balance = account_balance
                old_transaction.category.value = category_value
                old_transaction.account.save()
                old_transaction.category.save()
            elif new_transaction:
                new_transaction.account.balance = account_balance
                new_transaction.category.value = category_value
                new_transaction.account.save()
                new_transaction.category.save()

        return True
    except Exception as e:
        logging.error(f"Ошибка при обработке транзакции: {e}", exc_info=True)
        return False


@login_required
def update_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            try:
                # Сохраняем старую транзакцию
                old_transaction = Transaction.objects.get(id=transaction_id)

                # Создаём новую транзакцию из формы
                updated_transaction = form.save(commit=False)

                # Откат старой транзакции и применение новой
                success = process_transaction_change(old_transaction=old_transaction,
                                                     new_transaction=updated_transaction)

                if success:
                    updated_transaction.save()
                    logging.info(f"Транзакция успешно обновлена: ID={transaction_id}")
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Ошибка обработки транзакции'})
            except Exception as e:
                logging.error(f"Ошибка при обновлении транзакции: {e}", exc_info=True)
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        # Для отображения формы редактирования
        form = TransactionForm(instance=transaction)
        return render(request, 'ms/home/initial/transaction/transaction_form_partial.html', {'form': form})


@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'DELETE':
        # Обновление баланса категории и счета
        category = transaction.category
        account = transaction.account
        amount = transaction.amount

        if category.is_expense:
            account.balance += amount  # Возвращаем деньги в баланс счета
            category.value -= amount  # Уменьшаем значение категории расхода
        else:
            account.balance -= amount  # Снимаем деньги с баланса счета
            category.value -= amount  # Уменьшаем значение категории дохода

        # Сохраняем обновленные данные
        account.save()
        category.save()

        # Удаление транзакции
        transaction.delete()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


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


@require_http_methods(["POST"])
def delete_account(request, account_id):
    account = get_object_or_404(Account, id=account_id, user=request.user)

    if request.POST.get('_method') == 'DELETE':  # Проверка на имитацию метода DELETE
        account.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def convert_currency(request):
    try:
        # Получаем параметры из GET-запроса
        from_currency = request.GET.get('from')
        to_currency = request.GET.get('to')
        amount = Decimal(request.GET.get('amount', 0))

        # Проверяем, что все параметры переданы
        if not from_currency or not to_currency:
            return JsonResponse({'error': 'Missing currency parameters'}, status=400)

        # Получаем объекты валют
        from_currency_obj = Currency.objects.get(code=from_currency)
        to_currency_obj = Currency.objects.get(code=to_currency)

        # Расчет конверсии
        converted_amount = amount * from_currency_obj.rate_to_base / to_currency_obj.rate_to_base

        # Возврат результата
        return JsonResponse({'converted_amount': str(converted_amount)})

    except Currency.DoesNotExist as e:
        logger.error(f"Currency not found: {e}")
        return JsonResponse({'error': 'Currency not found'}, status=400)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


def transfer_between_accounts(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            source_account_id = data['source_account']
            target_account_id = data['target_account']
            amount = Decimal(data['amount'])

            source_account = get_object_or_404(Account, id=source_account_id, user=request.user)
            target_account = get_object_or_404(Account, id=target_account_id, user=request.user)

            if source_account.balance < amount:
                return JsonResponse({'error': 'Недостаточно средств'}, status=400)

            # Рассчитываем конвертированную сумму
            source_rate = source_account.currency.rate_to_base
            target_rate = target_account.currency.rate_to_base
            converted_amount = amount * (source_rate / target_rate)

            with transaction.atomic():
                source_account.balance -= amount
                target_account.balance += converted_amount
                source_account.save()
                target_account.save()

                # Добавляем запись в Transfer с указанием текущего пользователя
                Transfer.objects.create(
                    user=request.user,  # Указываем текущего пользователя
                    source_account=source_account,
                    target_account=target_account,
                    amount=converted_amount,
                    description=f"Перевод {amount} {source_account.currency.code} -> {converted_amount} {target_account.currency.code}"
                )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def transfer_transaction(request):
    if request.method == "POST":
        data = json.loads(request.body)
        source_account_id = data.get('source_account')
        target_account_id = data.get('target_account')
        amount = data.get('amount')

        if not (source_account_id and target_account_id and amount):
            return JsonResponse({"success": False, "error": "Недостаточно данных для перевода."})

        try:
            source_account = Account.objects.get(id=source_account_id)
            target_account = Account.objects.get(id=target_account_id)

            with transaction.atomic():
                # Транзакция списания
                Transaction.objects.create(
                    account=source_account,
                    amount=-float(amount),
                    category="Перевод",
                    description=f"Перевод на счёт {target_account.name}",
                )

                # Транзакция пополнения
                Transaction.objects.create(
                    account=target_account,
                    amount=float(amount),
                    category="Перевод",
                    description=f"Перевод со счёта {source_account.name}",
                )

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


def transfer_list(request):
    # Получаем переводы только для текущего пользователя
    transfers = Transfer.objects.filter(user=request.user).select_related('source_account', 'target_account')

    result = [
        {
            "id": transfer.id,
            "source_account": {
                "name": transfer.source_account.name,
                "currency": transfer.source_account.currency.code,
            },
            "target_account": {
                "name": transfer.target_account.name,
                "currency": transfer.target_account.currency.code,
            },
            "amount": transfer.amount,
            "transaction_date": transfer.transaction_date.isoformat(),
            "description": transfer.description,
        }
        for transfer in transfers
    ]

    return JsonResponse({"success": True, "transfers": result})


def transfer_list(request):
    # Получаем переводы только для текущего пользователя
    transfers = Transfer.objects.filter(user=request.user).select_related('source_account', 'target_account')

    result = [
        {
            "id": transfer.id,
            "source_account": {
                "name": transfer.source_account.name,
                "currency": transfer.source_account.currency.code,
            },
            "target_account": {
                "name": transfer.target_account.name,
                "currency": transfer.target_account.currency.code,
            },
            "amount": transfer.amount,
            "transaction_date": transfer.transaction_date.isoformat(),
            "description": transfer.description,
        }
        for transfer in transfers
    ]

    return JsonResponse({"success": True, "transfers": result})


@csrf_exempt
def delete_transfer(request, transfer_id):
    if request.method == 'DELETE':
        try:
            transfer = get_object_or_404(Transfer, id=transfer_id)

            source_account = transfer.source_account
            target_account = transfer.target_account
            converted_amount = transfer.amount

            # Рассчитываем обратное преобразование суммы
            source_rate = source_account.currency.rate_to_base
            target_rate = target_account.currency.rate_to_base
            original_amount = converted_amount * (target_rate / source_rate)

            with transaction.atomic():
                # Возврат средств
                source_account.balance += original_amount
                target_account.balance -= converted_amount

                # Сохранение изменений
                source_account.save()
                target_account.save()

                # Удаление записи о переводе
                transfer.delete()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Неверный метод запроса'}, status=405)


def filter_transfers(request):
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

    transfers = Transfer.objects.filter(**filters)

    result = [
        {
            "id": transfer.id,
            "source_account": {
                "name": transfer.source_account.name,
                "currency": transfer.source_account.currency.code,
            },
            "target_account": {
                "name": transfer.target_account.name,
                "currency": transfer.target_account.currency.code,
            },
            "amount": transfer.amount,
            "transaction_date": transfer.transaction_date.isoformat(),
            "description": transfer.description,
        }
        for transfer in transfers
    ]

    return JsonResponse({"success": True, "transfers": result})


@login_required
def get_currencies(request):
    currencies = Currency.objects.all().values('code', 'name')
    return JsonResponse({'currencies': list(currencies)})


@login_required
def update_currency(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        currency_code = data.get('currency')

        try:
            currency = Currency.objects.get(code=currency_code)
            request.user.profile.default_currency = currency  # Пример хранения валюты в профиле пользователя
            request.user.profile.save()

            return JsonResponse({'success': True})
        except Currency.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Валюта не найдена'})

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@login_required
def current_currency(request):
    profile = request.user.profile  # Получаем профиль пользователя
    currency = profile.default_currency.code if profile.default_currency else None
    return JsonResponse({'currency': currency})


def your_view(request):
    current_currency = request.user.profile.default_currency
    return render(request, 'your_template.html', {'current_currency': current_currency})
