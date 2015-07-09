from django.core.urlresolvers import reverse
from rest_framework import status
from shop.tests.factories import ProductFactory
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet.enums import TrxStatus
from wallet import api as wallet_api
from foobar.rest.fields import MoneyField
from ..factories import AccountFactory
from .base import AuthenticatedAPITestCase
from moneyed import Money


def serialize_money(x):
    return MoneyField().to_representation(x)


class TestPurchaseAPI(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.force_authenticate()

    def test_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK'),
            trx_status=TrxStatus.FINALIZED
        )
        product_obj1 = ProductFactory.create(
            name='Billys Ooriginal',
            price=Money(13, 'SEK')
        )
        product_obj2 = ProductFactory.create(
            name='Kebabrulle',
            price=Money(30, 'SEK')
        )
        url = reverse('api:purchases-list')
        data = {
            'account_id': account_obj.id,
            'products': [
                {'id': product_obj1.id, 'qty': 1},
                {'id': product_obj2.id, 'qty': 3},
            ]
        }
        response = self.api_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        _, balance = wallet_api.get_balance(wallet_obj.owner_id, 'SEK')
        self.assertEqual(balance, Money(897, 'SEK'))

    def test_purchase_insufficient_funds(self):
        account_obj = AccountFactory.create()
        product_obj1 = ProductFactory.create(
            price=Money(13, 'SEK')
        )
        product_obj2 = ProductFactory.create(
            price=Money(30, 'SEK')
        )
        url = reverse('api:purchases-list')
        data = {
            'account_id': account_obj.id,
            'products': [
                {'id': product_obj1.id, 'qty': 1},
                {'id': product_obj2.id, 'qty': 3},
            ]
        }
        response = self.api_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_purchase_invalid_quantity(self):
        account_obj = AccountFactory.create()
        product_obj1 = ProductFactory.create()
        product_obj2 = ProductFactory.create()
        url = reverse('api:purchases-list')
        data = {
            'account_id': account_obj.id,
            'products': [
                {'id': product_obj1.id, 'qty': -5},
                {'id': product_obj2.id, 'qty': 10},
            ]
        }
        response = self.api_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_purchase_invalid_product(self):
        account_obj = AccountFactory.create()
        url = reverse('api:purchases-list')
        data = {
            'account_id': account_obj.id,
            'products': [
                {'id': '6c91014d-f444-4ee7-906e-4e1737f7bc58', 'qty': 1},
            ]
        }
        response = self.api_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
