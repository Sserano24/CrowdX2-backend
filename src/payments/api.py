from ninja import Router
from django.http import JsonResponse, HttpResponse
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import redirect
from django.db.models import F
import requests

from .models import Transaction
from campaigns.models import Campaign  # ✅ Import Campaign model
from .services import (
    get_paypal_access_token,
    create_paypal_order,
    capture_paypal_order,
)


router = Router(tags=["Payments"])

@router.post("/paypal/create-order")
def create_order(request, amount: float, campaign_id: int):
    """Create a PayPal order and store it in the database"""
    try:
        order_data = create_paypal_order(amount)
        order_id = order_data.get("id")

        Transaction.objects.create(
            campaign_id=campaign_id,
            amount=amount,
            payment_method="paypal",
            status="pending",
            paypal_order_id=order_id,
        )

        return {
            "order_id": order_id,
            "links": order_data.get("links", []),
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@router.post("/paypal/capture-order")
def capture_order(request, order_id: str):
    """Capture an approved PayPal order and update campaign funding."""
    try:
        data = capture_paypal_order(order_id)
        status = data.get("status", "")

        tx = Transaction.objects.filter(paypal_order_id=order_id).first()
        if tx:
            tx.status = "completed" if status == "COMPLETED" else "failed"
            tx.payment_method = "paypal"
            tx.save()

            # ✅ Only update campaign funding if payment succeeded
            if tx.status == "completed":
                Campaign.objects.filter(id=tx.campaign_id).update(
                    current_amount=F("current_amount") + tx.amount
                )

        # ✅ Return redirect to frontend
        if status == "COMPLETED":
            return JsonResponse({"redirect": "/payment/success"})
        else:
            return JsonResponse({"redirect": "/payment/cancel"})
    except Exception as e:
        return JsonResponse({"redirect": "/payment/cancel", "error": str(e)}, status=400)

@router.post("/paypal/cancel")
def paypal_cancel(request, campaign_id: int = None, token: str = None):
    """Handle PayPal cancellation and mark the transaction as failed."""
    try:
        # 1️⃣ Update relevant transaction(s)
        if token:
            Transaction.objects.filter(paypal_order_id=token).update(
                status="failed",
                payment_method="paypal",
            )
        elif campaign_id:
            Transaction.objects.filter(
                campaign_id=campaign_id, status="pending"
            ).update(
                status="failed",
                payment_method="paypal",
            )

        # 2️⃣ Define redirect URL
        redirect_url = f"http://localhost:3000/payment/cancel"
        if campaign_id:
            redirect_url += f"?campaign_id={campaign_id}"

        # 3️⃣ Handle AJAX/fetch requests gracefully
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"message": "Transaction marked as failed", "redirect": redirect_url}
            )

        # 4️⃣ For browser-based redirects (like PayPal’s return)
        return redirect(redirect_url)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@router.get("/paypal/success")
def paypal_success(request, token: str = None, PayerID: str = None, campaign_id: int = None):
    """
    Handle PayPal returning a success redirect.
    Displays a nice confirmation and closes the popup automatically.
    """
    try:
        if token:
            Transaction.objects.filter(paypal_order_id=token).update(
                status="completed",
                payment_method="PayPal"
            )

        html = """
        <html>
          <head>
            <meta charset="UTF-8" />
            <title>Payment Successful | CrowdX</title>
            <style>
              body {
                background: linear-gradient(135deg, #FDE68A, #FBBF24);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                color: #333;
                margin: 0;
                animation: fadeIn 0.8s ease-in-out;
              }
              @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
              }
              .card {
                background: #fff;
                padding: 30px 40px;
                border-radius: 16px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 360px;
              }
              h1 {
                color: #16A34A;
                font-size: 1.8rem;
                margin-bottom: 10px;
              }
              p {
                font-size: 1rem;
                color: #555;
                margin-bottom: 20px;
              }
              .spinner {
                width: 32px;
                height: 32px;
                border: 4px solid #ccc;
                border-top-color: #16A34A;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
              }
              @keyframes spin {
                to { transform: rotate(360deg); }
              }
            </style>
          </head>
          <body>
            <div class="card">
              <div class="spinner"></div>
              <h1>Payment Successful!</h1>
              <p>Thank you for supporting this campaign.<br/>This window will close shortly.</p>
            </div>
            <script>
              setTimeout(() => {
                window.close();
              }, 3500);
            </script>
          </body>
        </html>
        """
        return HttpResponse(html)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@router.post("/paypal/webhook")
def paypal_webhook(request):
    """Handle PayPal webhook notifications safely."""
    import json
    from threading import Thread

    try:
        body = json.loads(request.body)
        event_type = body.get("event_type", "")
        resource = body.get("resource", {})
        print(f"🔔 Received PayPal Webhook: {event_type}")

        # ✅ Respond immediately so PayPal sees success
        def process_event():
            try:
                if event_type == "PAYMENT.CAPTURE.COMPLETED":
                    order_id = (
                        resource.get("supplementary_data", {})
                        .get("related_ids", {})
                        .get("order_id")
                    )
                    amount = float(resource.get("amount", {}).get("value", 0))
                    status = resource.get("status", "")

                    from .models import Transaction
                    tx = Transaction.objects.filter(paypal_order_id=order_id).first()
                    if tx:
                        tx.status = "completed" if status == "COMPLETED" else "failed"
                        tx.payment_method = "paypal"
                        tx.save()

                        # update campaign total
                        if status == "COMPLETED":
                            campaign = tx.campaign
                            campaign.amount_raised += amount
                            campaign.save()

                elif event_type == "PAYMENT.CAPTURE.DENIED":
                    order_id = (
                        resource.get("supplementary_data", {})
                        .get("related_ids", {})
                        .get("order_id")
                    )
                    Transaction.objects.filter(paypal_order_id=order_id).update(status="failed")
            except Exception as inner_e:
                print("⚠️ Error in async webhook processing:", inner_e)

        Thread(target=process_event).start()
        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        print("⚠️ Webhook error:", e)
        return JsonResponse({"error": str(e)}, status=400)


