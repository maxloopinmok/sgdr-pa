from django.conf import settings


def site_settings(request):
    """Expose a small whitelist of settings to all templates."""
    return {
        "GOATCOUNTER_SITE_CODE": getattr(settings, "GOATCOUNTER_SITE_CODE", ""),
    }
