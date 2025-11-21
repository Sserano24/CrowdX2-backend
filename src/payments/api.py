from ninja import Router
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.shortcuts import redirect
import requests
import json
from threading import Thread

from .models import Transaction
from campaigns.models import Campaign
from .services import (
    get_paypal_access_token,
    create_paypal_order,
    capture_paypal_order,
)

router = Router(tags=["Payments"])

# ✅ Estimate PayPal fee — preview only
@router.get("/paypal/estimate-fee")
def estimate_fee(request, amount: float):
    """Estimate PayPal fee without creating an order."""
    try:
        fee_percent = 0.0349
        fixed_fee = 0.49
        gross_amount = round((amount + fixed_fee) / (1 - fee_percent), 2)
        fee_added = round(gross_amount - amount, 2)
        message = f"A small PayPal processing fee of ${fee_added:.2f} has been added."

        return JsonResponse({
            "gross_amount": gross_amount,
            "fee_added": fee_added,
            "message": message
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ✅ Create order — actual DB + PayPal creation
@router.post("/paypal/create-order")
def create_order(request, amount: float, campaign_id: int):
    """Create a PayPal order and record the transaction."""
    try:
        fee_percent = 0.0349
        fixed_fee = 0.49
        gross_amount = round((amount + fixed_fee) / (1 - fee_percent), 2)
        fee_added = round(gross_amount - amount, 2)
        message = f"A small PayPal processing fee of ${fee_added:.2f} has been added."

        order_data = create_paypal_order(gross_amount)
        order_id = order_data.get("id")

        Transaction.objects.create(
            campaign_id=campaign_id,
            amount=gross_amount,
            payment_method="paypal",
            status="pending",
            paypal_order_id=order_id,
        )

        return {
            "order_id": order_id,
            "links": order_data.get("links", []),
            "gross_amount": gross_amount,
            "message": message,
        }

    except Exception as e:
        print("⚠️ Error creating PayPal order:", e)
        return JsonResponse({"error": str(e)}, status=400)

@router.post("/paypal/capture-order")
def capture_order(request, order_id: str):
    """Capture an approved PayPal order and update database with fee + net."""
    try:
        # Capture the PayPal order
        data = capture_paypal_order(order_id)
        status = data.get("status", "")

        # Extract breakdown info (PayPal fees, net, gross)
        purchase_units = data.get("purchase_units", [])
        breakdown = {}
        if purchase_units:
            payments = purchase_units[0].get("payments", {})
            captures = payments.get("captures", [])
            if captures:
                breakdown = captures[0].get("seller_receivable_breakdown", {})

        gross_value = float(breakdown.get("gross_amount", {}).get("value", 0))
        fee_value = float(breakdown.get("paypal_fee", {}).get("value", 0))
        net_value = float(breakdown.get("net_amount", {}).get("value", 0))

        # Update the transaction
        from .models import Transaction
        tx = Transaction.objects.filter(paypal_order_id=order_id).first()
        if tx:
            tx.status = "completed" if status == "COMPLETED" else "failed"
            tx.payment_method = "paypal"
            tx.amount = gross_value
            tx.fee = fee_value
            tx.net_amount = net_value
            tx.save()

            # Update campaign amount raised with net amount
            if status == "COMPLETED":
                campaign = tx.campaign
                campaign.current_amount = float(campaign.current_amount) + net_value
                campaign.save()


        # ✅ Redirect response for frontend
        if status == "COMPLETED":
            return JsonResponse({"redirect": "/payment/success"})
        else:
            return JsonResponse({"redirect": "/payment/cancel"})

    except Exception as e:
        print("⚠️ Capture error:", e)
        return JsonResponse({"redirect": "/payment/cancel", "error": str(e)}, status=400)



# ✅ 3. CANCEL ORDER — marks as failed
@router.post("/paypal/cancel")
def paypal_cancel(request, campaign_id: int = None, token: str = None):
    """Handle PayPal cancellation and mark the transaction as failed."""
    try:
        if token:
            Transaction.objects.filter(paypal_order_id=token).update(
                status="failed", payment_method="paypal"
            )
        elif campaign_id:
            Transaction.objects.filter(
                campaign_id=campaign_id, status="pending"
            ).update(status="failed", payment_method="paypal")

        redirect_url = f"http://localhost:3000/payment/cancel"
        if campaign_id:
            redirect_url += f"?campaign_id={campaign_id}"

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"message": "Transaction marked as failed", "redirect": redirect_url}
            )

        return redirect(redirect_url)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ✅ 4. SUCCESS PAGE — frontend popup closes after delay
@router.get("/paypal/success")
def paypal_success(request, token: str = None, PayerID: str = None, campaign_id: int = None):
    """Show confirmation and auto-close PayPal window."""
    try:
        if token:
            Transaction.objects.filter(paypal_order_id=token).update(
                status="completed", payment_method="paypal"
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
              @keyframes spin { to { transform: rotate(360deg); } }
            </style>
          </head>
          <body>
            <div class="card">
              <div class="spinner"></div>
              <h1>Payment Successful!</h1>
              <p>Thank you for supporting this campaign.<br/>This window will close shortly.</p>
            </div>
            <script>setTimeout(() => { window.close(); }, 3000);</script>
          </body>
        </html>
        """
        return HttpResponse(html)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@router.post("/paypal/webhook")
def paypal_webhook(request):
    """Handle PayPal webhook notifications and update campaign donations accurately."""
    try:
        body = json.loads(request.body)
        event_type = body.get("event_type", "")
        resource = body.get("resource", {})

        print(f"🔔 Received PayPal Webhook: {event_type}")

        def process_event():
            try:
                from .models import Transaction
                if event_type == "PAYMENT.CAPTURE.COMPLETED":
                    order_id = (
                        resource.get("supplementary_data", {})
                        .get("related_ids", {})
                        .get("order_id")
                    )

                    # ✅ Try both possible locations of seller_receivable_breakdown
                    breakdown = (
                        resource.get("seller_receivable_breakdown")
                        or resource.get("purchase_units", [{}])[0]
                        .get("payments", {})
                        .get("captures", [{}])[0]
                        .get("seller_receivable_breakdown", {})
                        or {}
                    )

                    gross_value = breakdown.get("gross_amount", {}).get("value")
                    fee_value = breakdown.get("paypal_fee", {}).get("value")
                    net_value = breakdown.get("net_amount", {}).get("value")
                    status = resource.get("status", "")

                    tx = Transaction.objects.filter(paypal_order_id=order_id).first()
                    if tx:
                        if tx.status != "completed":  # prevent duplicate updates
                            tx.status = "completed" if status == "COMPLETED" else "failed"
                            tx.payment_method = "paypal"
                            tx.amount = float(gross_value or tx.amount or 0)
                            tx.fee = float(fee_value or 0)
                            tx.net_amount = float(net_value or 0)
                            tx.save()

                        if status == "COMPLETED" and net_value:
                            campaign = tx.campaign
                            campaign.amount_raised += float(net_value)
                            campaign.save()

                elif event_type == "PAYMENT.CAPTURE.DENIED":
                    order_id = (
                        resource.get("supplementary_data", {})
                        .get("related_ids", {})
                        .get("order_id")
                    )
                    Transaction.objects.filter(paypal_order_id=order_id).update(status="failed")

            except Exception as inner_e:
                print("⚠️ Error processing webhook:", inner_e)

        Thread(target=process_event).start()
        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        print("⚠️ Webhook error:", e)
        return JsonResponse({"error": str(e)}, status=400)




