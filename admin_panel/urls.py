from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='admin_dashboard'),
    path('visitors/', views.visitors_list, name='admin_visitors'),
    # Expenses
    path('expenses/', views.expenses_list, name='admin_expenses'),
    path('expenses/delete/<int:expense_id>/', views.expense_delete, name='expense_delete'),
    
    # Cashbook
    path('cashbook/', views.cashbook_view, name='admin_cashbook'),
    
    path('management/', views.management, name='admin_management'),
    path('maintenance-settings/', views.maintenance_settings, name='maintenance_settings'),
    path('generate-bills/', views.generate_bills, name='generate_bills'),
    # Notices
    path('notices/', views.notices_list, name='notices_list'),
    path('notices/create/', views.notice_create, name='notice_create'),
    path('notices/delete/<int:notice_id>/', views.notice_delete, name='notice_delete'),
    
    # Complaints
    path('complaints/', views.complaints_list, name='complaints_list_admin'),
    path('complaints/resolve/<int:complaint_id>/', views.complaint_resolve, name='complaint_resolve'),
]
