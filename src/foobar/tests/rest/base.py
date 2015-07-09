from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from django.conf import settings
from authtoken.models import Token


class AuthenticatedAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.api_client = APIClient()

    def force_authenticate(self, user=None, token=None):
        if token is None:
            # No token provided so authenticate using a full access token
            token = Token()
            for scope, _ in settings.API_TOKEN_SCOPES:
                setattr(token.scopes, scope, True)
            token.save()

            # Set the default auth header for all requests
            token = 'Token {}'.format(token.key)
            self.api_client = APIClient(HTTP_AUTHORIZATION=token)

        self.api_client.force_authenticate(
            user=user,
            token=token
        )
