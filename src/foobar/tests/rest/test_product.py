import uuid
from django.core.urlresolvers import reverse_lazy as reverse
from rest_framework import status
from shop.tests.factories import (
    ProductFactory,
    ProductTrxFactory,
    ProductCategoryFactory
)
from shop.enums import TrxType
from foobar.rest.fields import MoneyField
from .base import AuthenticatedAPITestCase


def serialize_money(x):
    return MoneyField().to_representation(x)


class TestProductAPI(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.force_authenticate()

    def test_retrieve_existing(self):
        # retrieve an existing product
        product_obj = ProductFactory.create()
        ProductTrxFactory.create(
            product=product_obj,
            qty=10,
            trx_type=TrxType.INVENTORY
        )
        url = reverse('api:products-detail', kwargs={'pk': product_obj.id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['qty'], 10)
        # retrieve a non-existent product
        url = reverse('api:products-detail', kwargs={'pk': uuid.uuid4()})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_products(self):
        for code in range(9):
            ProductFactory.create()
        fixed_code = '1{0:012d}'.format(7331)
        ProductFactory.create(code=fixed_code)
        url = reverse('api:products-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

        # retrieve a single product by its code
        url = reverse('api:products-list')
        response = self.api_client.get(url, {'code': fixed_code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class TestProductCategoryAPI(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.force_authenticate()

    def test_list_categories(self):
        url = reverse('api:categories-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        ProductCategoryFactory.create()
        url = reverse('api:categories-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
