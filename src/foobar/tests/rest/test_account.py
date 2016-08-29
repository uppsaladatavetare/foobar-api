from django.core.urlresolvers import reverse
from rest_framework import status
from .base import AuthenticatedAPITestCase
from ..factories import CardFactory


class TestAccountAPI(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.force_authenticate()

    def test_retrieve(self):
        url = reverse('api:accounts-detail', kwargs={'pk': 1337})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse('api:accounts-detail', kwargs={'pk': (2 ** 64) - 1})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse('api:accounts-detail', kwargs={'pk': 'abc'})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        CardFactory.create(number=1337)
        url = reverse('api:accounts-detail', kwargs={'pk': 1337})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
