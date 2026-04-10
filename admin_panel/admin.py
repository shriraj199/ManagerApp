from django.contrib import admin
from .models import Visitor
from core.models import Expense

admin.site.register(Visitor)
admin.site.register(Expense)
