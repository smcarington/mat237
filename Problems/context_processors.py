from django.conf import settings

def site_name(request):
    return {
        "site_name": settings.SITE_NAME,
        "doc_choices": settings.DOC_CHOICES,
        "show_details": settings.SHOW_QUESTION_DETAILS,
    }
