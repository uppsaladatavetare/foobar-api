import django.dispatch


status_change = django.dispatch.Signal(
    providing_args=['from_status', 'to_status', 'direction']
)
