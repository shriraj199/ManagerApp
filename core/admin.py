from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, InviteCode, RentalChargeSettings

class CustomUserAdmin(UserAdmin):
    model = User
    
    list_display = ['email', 'username', 'role', 'resident_role', 'society_name', 'unit_number', 'is_staff']
    list_filter = ['role', 'resident_role', 'society_name', 'is_staff', 'is_active']
    search_fields = ['email', 'username', 'society_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Info', {'fields': ('role', 'resident_role', 'owner', 'society_name', 'mobile_number', 'unit_number', 'upi_id', 'upi_name')}),
    )

admin.site.register(User, CustomUserAdmin)

# Also register InviteCode so you can manage them in the admin!
@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'society_name', 'company', 'created_at']
    search_fields = ['code', 'society_name']
    list_filter = ['created_at']

@admin.register(RentalChargeSettings)
class RentalChargeSettingsAdmin(admin.ModelAdmin):
    list_display = ['owner', 'rental_user', 'monthly_rent', 'due_day', 'account_number', 'created_at']
    list_filter = ['due_day', 'created_at']
    search_fields = ['owner__username', 'rental_user__username', 'account_number']
