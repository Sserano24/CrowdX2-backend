import requests
import json
from django.conf import settings

def get_paypal_access_token():
    """Fetch OAuth token from PayPal."""
    url = f"{settings.PAYPAL_API_BASE}/v1/oauth2/token"
    response = requests.post(
        url,
        headers={"Accept": "application/json", "Accept-Language": "en_US"},
        data={"grant_type": "client_credentials"},
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
    )
    response.raise_for_status()
    return response.json()["access_token"]


def create_paypal_order(amount):
    """Create an order with PayPal."""
    access_token = get_paypal_access_token()
    url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": "USD", "value": str(amount)},
            }
        ],
        "application_context": {
            "brand_name": "CrowdX Sandbox",
            # 👇 this redirect auto-closes the popup
            "return_url": "http://127.0.0.1:8001/api/payments/paypal/success",
            "cancel_url": "http://127.0.0.1:8001/api/payments/paypal/cancel",
        },
    }

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()


def capture_paypal_order(order_id):
    """Capture an existing PayPal order after user approval."""
    access_token = get_paypal_access_token()
    url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()


def verify_paypal_webhook(request):
    """Verify webhook came from PayPal."""
    try:
        auth_token = get_paypal_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}",
        }
        body = {
            "auth_algo": request.headers.get("PAYPAL-AUTH-ALGO"),
            "cert_url": request.headers.get("PAYPAL-CERT-URL"),
            "transmission_id": request.headers.get("PAYPAL-TRANSMISSION-ID"),
            "transmission_sig": request.headers.get("PAYPAL-TRANSMISSION-SIG"),
            "transmission_time": request.headers.get("PAYPAL-TRANSMISSION-TIME"),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": json.loads(request.body.decode("utf-8")),
        }

        resp = requests.post(
            f"{settings.PAYPAL_API_BASE}/v1/notifications/verify-webhook-signature",
            json=body,
            headers=headers,
        )
        return resp.json().get("verification_status") == "SUCCESS"
    except Exception as e:
        print(f"Webhook verification error: {e}")
        return False
