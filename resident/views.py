from django.conf import settings
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Bill, Complaint
from django.utils import timezone
from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def dashboard(request):
    if request.user.role != 'resident':
        return redirect('admin_dashboard')

    bills = request.user.bills.filter(status='Pending')
    complaints = request.user.complaints.all()

    # Calculate total pending amount with dynamic late fees
    total_pending = Decimal('0.00')
    today = date.today()

    for bill in bills:
        if bill.due_date and today > bill.due_date:
            if not bill.is_late_applied:
                late_fee = bill.total_amount * Decimal('0.21')
                bill.late_fee_amount = late_fee
                bill.total_amount += late_fee
                bill.is_late_applied = True
                bill.save()
        total_pending += bill.total_amount

    context = {
        'bills_count': bills.count(),
        'total_pending': total_pending,
        'current_balance': request.user.get_maintenance_balance(),
        'complaints': complaints,
        'is_owner': request.user.resident_role == 'owner',
        'is_rental': request.user.resident_role == 'rental',
    }

    # For rental residents: show their rent info from their owner
    if request.user.resident_role == 'rental':
        try:
            from core.models import RentalChargeSettings
            rental_charge = RentalChargeSettings.objects.get(rental_user=request.user)
            context['rental_charge'] = rental_charge
        except:
            context['rental_charge'] = None

    # For owner residents: show count of their rentals
    if request.user.resident_role == 'owner':
        from core.models import RentalChargeSettings
        context['rental_count'] = RentalChargeSettings.objects.filter(owner=request.user).count()

    # --- SOCIETY NOTICES ---
    from core.models import Notice
    context['notices'] = Notice.objects.filter(society_name=request.user.society_name).order_by('-created_at')[:5]

    # --- ONE-TIME WELCOME POPUP ---
    context['show_welcome'] = not request.user.has_seen_welcome
    if not request.user.has_seen_welcome:
        request.user.has_seen_welcome = True
        request.user.save(update_fields=['has_seen_welcome'])

    return render(request, 'resident/dashboard.html', context)


@login_required
def bills_list(request):
    if request.user.role != 'resident':
        return redirect('admin_dashboard')

    bills = request.user.bills.all().order_by('-year', '-month')
    today = date.today()

    for bill in bills:
        if bill.status == 'Pending' and bill.due_date and today > bill.due_date:
            if not bill.is_late_applied:
                late_fee = bill.total_amount * Decimal('0.21')
                bill.late_fee_amount = late_fee
                bill.total_amount += late_fee
                bill.is_late_applied = True
                bill.save()

    return render(request, 'resident/bills.html', {
        'bills': bills,
        'today': today,
        'is_owner': request.user.resident_role == 'owner',
        'is_rental': request.user.resident_role == 'rental',
    })


@login_required
def complaints_list(request):
    if request.user.role != 'resident':
        return redirect('admin_dashboard')
    complaints = request.user.complaints.all()
    return render(request, 'resident/complaints.html', {'complaints': complaints})


@login_required
def more_options(request):
    if request.user.role != 'resident':
        return redirect('admin_dashboard')
    return render(request, 'resident/more.html', {
        'is_owner': request.user.resident_role == 'owner',
        'is_rental': request.user.resident_role == 'rental',
    })


@login_required
def receipt_view(request, bill_id):
    if request.user.role != 'resident':
        return redirect('admin_dashboard')
    bill = get_object_or_404(Bill, id=bill_id, user=request.user, status='Paid')
    return render(request, 'resident/receipt.html', {'bill': bill})


@login_required
def generate_receipt_pdf(request, bill_id):
    if request.user.role != 'resident':
        return redirect('admin_dashboard')
    bill = get_object_or_404(Bill, id=bill_id, user=request.user, status='Paid')

    logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'pwa', 'logo.png')
    context = {
        'bill': bill,
        'logo_path': logo_path
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{bill.id}.pdf"'

    template_path = 'resident/receipt_pdf.html'
    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


# ─── Owner: Rental Management ─────────────────────────────────────────────────

@login_required
def rental_management(request):
    """Owner can see all their rental settings and manage them."""
    if request.user.role != 'resident' or request.user.resident_role != 'owner':
        return redirect('resident_dashboard')

    from core.models import RentalChargeSettings, RentPaymentProof
    rentals = RentalChargeSettings.objects.filter(owner=request.user).select_related('rental_user')
    
    # All tenant accounts created/owned by this owner
    all_tenants = User.objects.filter(
        role='resident', resident_role='rental',
        owner=request.user
    )

    # Rent proofs received by this owner
    rent_proofs = RentPaymentProof.objects.filter(owner=request.user).order_by('-created_at')

    return render(request, 'resident/rental_management.html', {
        'rentals': rentals,
        'all_tenants': all_tenants,
        'rent_proofs': rent_proofs,
    })


@login_required
def rental_add_profile(request):
    """Owner creates a new rental (tenant) user account directly from their portal."""
    if request.user.role != 'resident' or request.user.resident_role != 'owner':
        return redirect('resident_dashboard')

    if request.method == 'POST':
        from django.contrib.auth import get_user_model
        from django.db import IntegrityError
        User_ = get_user_model()

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        unit_number = request.user.unit_number # Locked to owner's unit
        password = request.POST.get('password', '').strip()

        if not email or not password or not full_name:
            messages.error(request, 'Full name, email and password are required.')
            return render(request, 'resident/rental_add_profile.html')

        if User_.objects.filter(username=email).exists():
            messages.error(request, f'An account with email "{email}" already exists.')
            return render(request, 'resident/rental_add_profile.html')

        try:
            rental_user = User_.objects.create_user(
                username=email,
                email=email,
                first_name=full_name,
                password=password,
                role='resident',
                resident_role='rental',
                mobile_number=mobile,
                society_name=request.user.society_name,
                unit_number=unit_number,
                owner=request.user,
            )
            messages.success(request, f'✅ Rental profile for {full_name} created! They can now log in with {email}.')
            return redirect('rental_management')
        except IntegrityError:
            messages.error(request, 'Could not create account. Please try again.')
            return render(request, 'resident/rental_add_profile.html')

    return render(request, 'resident/rental_add_profile.html')


@login_required
def rental_tenant_delete(request, tenant_id):
    """Owner can delete a rental tenant's account they created."""
    if request.user.role != 'resident' or request.user.resident_role != 'owner':
        return redirect('resident_dashboard')

    tenant = get_object_or_404(User, id=tenant_id, role='resident', resident_role='rental', owner=request.user)
    name = tenant.first_name or tenant.username
    tenant.delete()
    messages.success(request, f'Rental profile for {name} has been removed.')
    return redirect('rental_management')


@login_required
def rental_charge_create(request):
    """Owner creates a new rental charge setting."""
    if request.user.role != 'resident' or request.user.resident_role != 'owner':
        return redirect('resident_dashboard')

    from core.models import RentalChargeSettings

    # Already-linked rental users
    linked_ids = RentalChargeSettings.objects.filter(owner=request.user).values_list('rental_user_id', flat=True)
    available_rentals = User.objects.filter(
        role='resident', resident_role='rental',
        society_name=request.user.society_name,
        owner=request.user
    ).exclude(id__in=linked_ids)

    if request.method == 'POST':
        rental_user_id = request.POST.get('rental_user_id')
        monthly_rent = request.POST.get('monthly_rent', 0)
        due_day = request.POST.get('due_day', 5)
        account_number = request.POST.get('account_number', '')
        notes = request.POST.get('notes', '')

        rental_user = None
        if rental_user_id:
            rental_user = User.objects.filter(id=rental_user_id, role='resident', resident_role='rental', owner=request.user).first()

        rc = RentalChargeSettings.objects.create(
            owner=request.user,
            rental_user=rental_user,
            monthly_rent=monthly_rent,
            due_day=due_day,
            account_number=account_number,
            notes=notes,
        )

        if request.FILES.get('rent_qr'):
            rc.rent_qr = request.FILES.get('rent_qr')
            rc.save()

        messages.success(request, "✅ Rental charge settings created successfully!")
        return redirect('rental_management')

    return render(request, 'resident/rental_charge_form.html', {
        'available_rentals': available_rentals,
        'form_title': 'Create Rental Charge',
        'submit_label': 'Create',
    })


@login_required
def rental_charge_edit(request, rc_id):
    """Owner edits an existing rental charge."""
    if request.user.role != 'resident' or request.user.resident_role != 'owner':
        return redirect('resident_dashboard')

    from core.models import RentalChargeSettings
    rc = get_object_or_404(RentalChargeSettings, id=rc_id, owner=request.user)

    # Rentals available to link (excluding already-linked ones from OTHER settings)
    linked_ids = RentalChargeSettings.objects.filter(owner=request.user).exclude(id=rc.id).values_list('rental_user_id', flat=True)
    available_rentals = User.objects.filter(
        role='resident', resident_role='rental',
        society_name=request.user.society_name,
        owner=request.user
    ).exclude(id__in=linked_ids)

    if request.method == 'POST':
        rental_user_id = request.POST.get('rental_user_id')
        rc.monthly_rent = request.POST.get('monthly_rent', rc.monthly_rent)
        rc.due_day = request.POST.get('due_day', rc.due_day)
        rc.account_number = request.POST.get('account_number', rc.account_number)
        rc.notes = request.POST.get('notes', rc.notes)

        if rental_user_id:
            rental_user = User.objects.filter(id=rental_user_id, role='resident', resident_role='rental', owner=request.user).first()
            rc.rental_user = rental_user

        if request.FILES.get('rent_qr'):
            rc.rent_qr = request.FILES.get('rent_qr')

        rc.save()
        messages.success(request, "✅ Rental charge updated successfully!")
        return redirect('rental_management')

    return render(request, 'resident/rental_charge_form.html', {
        'rc': rc,
        'available_rentals': available_rentals,
        'form_title': 'Edit Rental Charge',
        'submit_label': 'Save Changes',
    })


@login_required
def rental_charge_delete(request, rc_id):
    """Owner deletes a rental charge setting."""
    if request.user.role != 'resident' or request.user.resident_role != 'owner':
        return redirect('resident_dashboard')

    from core.models import RentalChargeSettings
    rc = get_object_or_404(RentalChargeSettings, id=rc_id, owner=request.user)
    rc.delete()
    messages.success(request, "Rental charge deleted.")
    return redirect('rental_management')


@login_required
def rental_dashboard(request):
    """Rental resident sees their rent details set by their owner."""
    if request.user.role != 'resident' or request.user.resident_role != 'rental':
        return redirect('resident_dashboard')

    from core.models import RentalChargeSettings
    try:
        rental_charge = RentalChargeSettings.objects.get(rental_user=request.user)
    except RentalChargeSettings.DoesNotExist:
        rental_charge = None

    return render(request, 'resident/rental_dashboard.html', {
        'rental_charge': rental_charge,
        'owner': request.user.owner,
    })
