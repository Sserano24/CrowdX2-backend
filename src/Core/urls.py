from payments.webhooks import paypal_webhook
from django.contrib import admin
from django.urls import path, include
from .api import api  # TEMP disabled to bypass pydantic/ninja_jwt crash

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),  # TEMP disabled
    path("api/payments/paypal/webhook/", paypal_webhook),
    path("api/payments/", include("payments.urls")),
]

# Health check endpoint
from django.http import JsonResponse
def health(request):
    return JsonResponse({"ok": True})
urlpatterns.append(path("health/", health))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
