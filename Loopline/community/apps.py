from django.apps import AppConfig


# This class was already here
class CommunityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "community"

    def ready(self):
        import os
        from django.conf import settings

        # Import signals so they get registered
        try:
            import community.signals
        except Exception:
            # Signals may fail to import during certain management commands; ignore silently
            pass
        try:
            from django.contrib.sites.models import Site

            site_domain = (
                os.getenv("SITE_DOMAIN", None) or f"{settings.ALLOWED_HOSTS[0]}:8000"
            )
            site_name = os.getenv("SITE_NAME", site_domain)
            site, created = Site.objects.get_or_create(pk=settings.SITE_ID)
            if site.domain != site_domain or site.name != site_name:
                site.domain = site_domain
                site.name = site_name
                site.save()
        except Exception:
            pass
