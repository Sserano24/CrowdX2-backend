from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.views import View
import stripe
from .models import Project

# Initialize Stripe with secret key from environment
stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------- BASIC PAGES ----------
def home(request):
    return render(request, "campaign/index.html")

def projects(request):
    projects = Project.objects.all()
    return render(request, "campaign/projects.html", {"projects": projects})

def create_project(request):
    return render(request, "campaign/create_project.html")

def signup(request):
    return render(request, "campaign/signup.html")

def login(request):
    return render(request, "campaign/login.html")

def about(request):
    return render(request, "campaign/about.html")

def contact(request):
    return render(request, "campaign/contact.html")

def cancel(request):
    return render(request, "campaign/cancel.html")

def success(request):
    return render(request, "campaign/success.html")

def payment(request):
    return render(request, "campaign/payment.html")

def project_detail(request, id):
    return render(request, "campaign/project_detail.html", {"id": id})


# ---------- STRIPE CHECKOUT ----------
class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        """Create a Stripe Checkout session using the posted amount."""
        amount = request.POST.get("amount")
        if not amount:
            return JsonResponse({"error": "Invalid amount"}, status=400)

        try:
            amount_in_cents = int(float(amount) * 100)

            # Dynamic success/cancel URLs (auto match dev or prod)
            success_url = request.build_absolute_uri("/success/")
            cancel_url = request.build_absolute_uri("/cancel/")

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": "CrowdX Custom Payment"},
                            "unit_amount": amount_in_cents,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
            )
            # Redirect user to Stripe Checkout page
            return redirect(checkout_session.url)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# ---------- HEALTH ENDPOINT ----------
def health(request):
    """Used by Render health checks and for quick status testing."""
    return JsonResponse({"ok": True})
