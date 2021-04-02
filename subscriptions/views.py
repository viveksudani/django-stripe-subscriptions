import os
import stripe
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse


@login_required
def home(request):
    return render(request, 'home.html')


@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
        stripe_config = {'publicKey': STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        domain_url = os.getenv('DOMAIN_URL')
        user_id = request.user.id if request.user.is_authenticated else None
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=user_id,
                success_url=domain_url +
                'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancel/',
                payment_method_types=['card'],
                mode='subscription',
                line_items=[
                    {
                        'price': os.getenv('STRIPE_PRICE_ID'),
                        'quantity': 1,
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})


@login_required
def success(request):
    return render(request, 'success.html')


@login_required
def cancel(request):
    return render(request, 'cancel.html')
