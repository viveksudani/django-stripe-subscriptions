import os
import stripe
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse, HttpResponse
from django.contrib.auth.models import User

from . models import StripeCustomer

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')


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
        stripe.api_key = STRIPE_SECRET_KEY
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


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = STRIPE_SECRET_KEY
    endpoint_secret = STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        print("Error occured during processing webhook data /n", str(e))
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("Error occured during processing webhook data /n", str(e))
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Fetch all the required data from session
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get('subscription')

        # Get the user and create a new StripeCustomer
        user = User.objects.get(id=client_reference_id)
        StripeCustomer.objects.create(
            user=user,
            stripeCustomerId=stripe_customer_id,
            stripeSubscriptionId=stripe_subscription_id,
        )
        print(user.username + ' just subscribed.')

    return HttpResponse(status=200)
