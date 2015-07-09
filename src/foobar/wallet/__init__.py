"""
Foobar is meant to be used for small, local shops, so we do not need
more than one currency. This module acts as a proxy that sets
the default currency on all the API calls in the wallet module.
"""
import moneyed
from functools import partial
from django.conf import settings


Money = partial(moneyed.Money, currency=settings.DEFAULT_CURRENCY)
