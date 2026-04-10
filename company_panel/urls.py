from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='company_dashboard'),
    path('generate_code/', views.generate_code, name='generate_code'),
]
