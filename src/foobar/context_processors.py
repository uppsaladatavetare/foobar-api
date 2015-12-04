def thunderpush_settings(request):
    from django.conf import settings
    return {
        'THUNDERPUSH_HOST': settings.THUNDERPUSH_HOST,
        'THUNDERPUSH_APIKEY': settings.THUNDERPUSH_APIKEY,
        'THUNDERPUSH_PROTO': settings.THUNDERPUSH_PROTO
    }
