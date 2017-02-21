import datetime
import jwt

from django.conf.urls import url
from django.http import HttpResponse
from django.test import override_settings, TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

from .authentication import FooCardAuthentication
from .models import Token
from .views import obtain_foocard_token
from foobar.models import Account
from foobar.tests.factories import AccountFactory, CardFactory

factory = APIRequestFactory()


class MockView(APIView):
    def get(self, request):
        return HttpResponse({'some': 1, 'thing': 2, 'dandy': 3})

    def post(self, request):
        return HttpResponse({'some': 1, 'thing': 2, 'dandy': 3})

    def put(self, request):
        return HttpResponse({'some': 1, 'thing': 2, 'dandy': 3})


urlpatterns = [
    url(r'^cardtoken/$',
        MockView.as_view(authentication_classes=[FooCardAuthentication])),
    url(r'^auth-token/$', obtain_foocard_token),
]


@override_settings(ROOT_URLCONF='authtoken.test', SECRET_WEBTOKEN='secret')
class AuthenticateFooCardTokenTests(TestCase):
    enc = 'HS256'
    path = '/cardtoken/'

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)

    def test_correct_auth_of_token(self):
        account = AccountFactory()
        token = jwt.encode(
            {'account_id': str(account.pk)},
            'secret',
            algorithm=self.enc
        )
        auth = 'CardToken {0}'.format(token.decode())
        response = self.csrf_client.post(
            self.path,
            {'example': 'example'},
            format='json',
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_auth_with_invalid_token(self):
        token = jwt.encode(
            {'some': 'payload'},
            'invalidsecret',
            algorithm=self.enc
        )
        auth = 'CardToken {0}'.format(token.decode())
        response = self.csrf_client.post(
            self.path,
            {'example': 'example'},
            format='json',
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_with_expired_token(self):
        stamp = timezone.now() - datetime.timedelta(minutes=10)
        token = jwt.encode({'exp': stamp}, 'secret', algorithm=self.enc)
        auth = 'CardToken {0}'.format(token.decode())
        response = self.csrf_client.get(
            self.path,
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_with_bad_account(self):
        AccountFactory()  # Keep this here so we just don't have an empty QS
        stamp = timezone.now() + datetime.timedelta(minutes=10)
        token = jwt.encode(
            {'exp': stamp, 'account_id': None},
            'secret',
            algorithm=self.enc
        )
        auth = 'CardToken {0}'.format(token.decode())
        response = self.csrf_client.get(
            self.path,
            {'example': 'example'},
            format='json',
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_with_bad_header(self):
        account = AccountFactory()
        stamp = timezone.now() + datetime.timedelta(minutes=10)
        token = jwt.encode(
            {'exp': stamp, 'account_id': str(account.pk)},
            'secret',
            algorithm=self.enc
        )
        auth = 'ThisIsIncorrect {0}'.format(token.decode())
        response = self.csrf_client.get(
            self.path,
            {'exp': stamp, 'account_id': str(account.pk)},
            format='json',
            HTTP_AUTHORIZATION=auth
        )
        # Returns 200_OK as it is not allowed to even try to authenticate
        # And there is no other authentication that is tested
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        auth = 'CardToken'
        response = self.csrf_client.get(
            self.path,
            {'exp': stamp, 'account_id': str(account.pk)},
            format='json',
            HTTP_AUTHORIZATION=auth
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        auth = 'CardToken {0} {1}'.format(token.decode()[:10], token.decode())
        response = self.csrf_client.get(
            self.path,
            {'exp': stamp, 'account_id': str(account.pk)},
            format='json',
            HTTP_AUTHORIZATION=auth
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(ROOT_URLCONF='authtoken.test', SECRET_WEBTOKEN='secret')
class CreateFooCardTokenTests(TestCase):
    enc = 'HS256'
    path = '/auth-token/'

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)

    def test_create_new_account_token(self):
        card = CardFactory()
        api_token = Token.objects.create(key='abc123')
        auth = 'Token {0}'.format(api_token)
        response = self.csrf_client.post(
            self.path,
            {'number': card.number},
            format='json',
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('card_token', response.data.keys())

        token = response.data.get('card_token')
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 0)

        try:
            decoded = jwt.decode(token, 'secret', algorithm=self.enc)
        except jwt.exceptions.InvalidTokenError as e:
            self.fail(e)

        account = Account.objects.all().first()
        self.assertEqual(decoded.get('account_id'), str(account.pk))
        self.assertIn('exp', decoded.keys())

    def test_create_token_for_invalid_account(self):
        api_token = Token.objects.create(key='abc123')
        auth = 'Token {0}'.format(api_token)
        response = self.csrf_client.post(
            self.path,
            {'number': '123456'},
            format='json',
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('number', response.data.keys())

    def test_create_token_with_incorrect_data(self):
        api_token = Token.objects.create(key='abc123')
        auth = 'Token {0}'.format(api_token)
        response = self.csrf_client.post(
            self.path,
            {'sumtinwong': '123456'},
            format='json',
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('number', response.data.keys())

        response = self.csrf_client.post(
            self.path,
            {'number': ''},
            format='json',
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('number', response.data.keys())

        response = self.csrf_client.post(
            self.path,
            {'number': None},
            format='json',
            HTTP_AUTHORIZATION=auth
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('number', response.data.keys())
