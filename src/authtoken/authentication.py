import jwt
from jwt.exceptions import InvalidKeyError, InvalidTokenError
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework import authentication, exceptions
from rest_framework.authentication import get_authorization_header

from .models import Token
from foobar.models import Account


def validate_header(auth):
    if len(auth) == 1:
        msg = _('Invalid token header. No credentials provided.')
        raise exceptions.AuthenticationFailed(msg)
    elif len(auth) > 2:
        msg = _('Invalid token header. Token string should not contain '
                'spaces.')
        raise exceptions.AuthenticationFailed(msg)


class FallbackAuthentication(authentication.BaseAuthentication):
    """
    This is a fallback intended to run as a last resort for authentication.
    It does however only raise an exception, telling the requestor that all
    attempts on authenticating has failed.
    """

    def authenticate(self):
        raise exceptions.AuthenticationFailed(_('Invalid token'))


class TokenAuthentication(authentication.BaseAuthentication):
    """
    Simple token based authentication.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:
        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    model = Token
    """
    A custom token model may be used, but must have the following properties.
    * key -- The string identifying the token
    * user -- The user to which the token belongs
    """

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != b'token':
            return None

        validate_header(auth)
        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain '
                    'invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        return (None, token)

    def authenticate_header(self, request):
        return 'Token'


class FooCardAuthentication(authentication.BaseAuthentication):
    """
    JSON Web Token authentication.
    Acts identically to token based authentication, as seen from the outside.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "CardToken ". For example:
        Authorization: CardToken: 401f7ac837da42b97f613d789819ff93537bee6a
    """
    algorithm = 'HS256'
    message = 'Invalid token'
    model = Account

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != b'cardtoken':
            return None

        validate_header(auth)
        try:
            payload = jwt.decode(
                auth[1].decode(),
                settings.SECRET_WEBTOKEN,
                algorithm=self.algorithm
            )
        except (InvalidKeyError, InvalidTokenError):
            msg = _('{0} header'.format(self.message))
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(payload)

    def authenticate_credentials(self, payload):
        account_id = payload.get('account_id')
        try:
            account = self.model.objects.get(pk=account_id)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_(self.message))

        return (account, None)

    def authenticate_header(self, request):
        return 'CardToken'
