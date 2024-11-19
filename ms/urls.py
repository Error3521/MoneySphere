from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name="home"),
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("initial/", views.initial_page, name="initial_page"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),


    path("initial/categories/", views.categories_combined_view, name="categories"),
    path('initial/categories/create/', views.create_category, name='create_category'),
    path('api/category/<int:category_id>/', views.get_category_data, name='get_category_data'),
    path('api/category/<int:category_id>/update/', views.update_category, name='update_category'),
    path('api/category/<str:category_id>/delete/', views.delete_category, name='delete_category'),
    path("api/categories/filter/", views.filter_categories, name="filter_categories"),


    path('initial/transaction/', views.transactions_view, name='transactions'),
    path('initial/transaction/create/', views.create_transaction, name='create_transaction'),
    path('initial/transaction/<int:transaction_id>/update/', views.update_transaction, name='update_transaction'),
    path('initial/transaction/<int:transaction_id>/delete/', views.delete_transaction, name='delete_transaction'),
    path('initial/transaction/filter/', views.filter_transactions, name='filter_transactions'),


    path('initial/accounts/', views.accounts_view, name='accounts'),
    path('initial/accounts/create/', views.create_account, name='create_account'),
    path('initial/accounts/<int:account_id>/update/', views.update_account, name='update_account'),
    path('initial/accounts/<int:account_id>/delete/', views.delete_account, name='delete_account'),




]
