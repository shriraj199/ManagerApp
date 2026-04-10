import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
try:
    import razorpay
except ImportError:
    razorpay = None

from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

@csrf_exempt
def verify_upi(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            upi_id = data.get('upi_id')
            
            if not upi_id:
                return JsonResponse({'status': 'error', 'message': 'UPI ID is required'}, status=400)

            # Fallback for development if keys are not set
            if getattr(settings, 'RAZORPAY_KEY_ID', '') == 'YOUR_RAZORPAY_KEY_ID' or '@' not in upi_id:
                mock_names = {
                    'shriram@upi': 'Shriram Iyer',
                    'test@upi': 'Test User'
                }
                fetched_name = mock_names.get(upi_id, "Verified User (Mock)")
                return JsonResponse({'status': 'success', 'upi_name': fetched_name})

            # Actual Razorpay VPA Verification logic
            if not razorpay:
                return JsonResponse({'status': 'error', 'message': 'Razorpay library not installed'}, status=500)

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            try:
                res = client.vpa.validate({"vpa": upi_id})
                if res.get('success'):
                    return JsonResponse({'status': 'success', 'upi_name': res.get('customer_name') or 'Verified User'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Invalid VPA or verification failed'}, status=400)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Razorpay Error: {str(e)}'}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('email') # Using email as username for simplicity
            email = data.get('email')
            full_name = data.get('full_name', '')
            password = data.get('password')
            role = data.get('role')
            mobile_number = data.get('mobile_number')
            invite_code = data.get('invite_code')
            
            if role in ['secretary', 'resident']:
                if not invite_code:
                    return JsonResponse({'status': 'error', 'message': 'Invite code is required'}, status=400)
                
                from .models import InviteCode
                invite_obj = InviteCode.objects.filter(code=invite_code).first()
                if not invite_obj:
                    return JsonResponse({'status': 'error', 'message': 'Invalid invite code'}, status=400)
                
                society_name = invite_obj.society_name
                
                if role == 'secretary':
                    existing_secretary = User.objects.filter(role='secretary', society_name=society_name).exists()
                    if existing_secretary:
                        return JsonResponse({'status': 'error', 'message': 'A secretary already exists for this society'}, status=400)
            else:
                society_name = None
            upi_id = data.get('upi_id')
            upi_name = data.get('upi_name')
            unit_number = data.get('unit_number', '')

            if not all([email, password, role]):
                return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=full_name,
                password=password,
                role=role,
                mobile_number=mobile_number,
                society_name=society_name,
                upi_id=upi_id,
                upi_name=upi_name,
                unit_number=unit_number
            )
            
            return JsonResponse({'status': 'success', 'message': 'User registered successfully'})
        except IntegrityError:
            return JsonResponse({'status': 'error', 'message': 'Email already registered'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
