import functools
import logging
from django.core import signing
from django.shortcuts import render
from .. import api

log = logging.getLogger(__name__)


def token_required(f):
    """Make sure the token is correct and provide the associated account."""
    @functools.wraps(f)
    def wrapper(request, *args, **kwargs):
        try:
            token = kwargs.get('token', None)
            data = signing.loads(token, max_age=1800)
        except signing.BadSignature:
            return render(request, 'profile/invalid_token.html', status=403)
        kwargs['account'] = api.get_account(data.get('id'))
        if kwargs['account'] is None:
            log.warning('Received token for a non-existing account: %s.',
                        data.get('id'))
            return render(request, 'profile/invalid_token.html', status=403)
        return f(request, *args, **kwargs)
    return wrapper
