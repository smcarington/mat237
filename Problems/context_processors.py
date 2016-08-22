from django.conf import settings

def site_name(request):
    return {
        "site_name": settings.SITE_NAME,
        "doc_choices": settings.DOC_CHOICES,
    }
