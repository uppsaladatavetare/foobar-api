import uuid
from django.core.urlresolvers import reverse_lazy as reverse
from django.conf import settings
from rest_framework import status
from shop.tests.factories import ProductFactory
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet import enums, api as wallet_api
from foobar.rest.fields import MoneyField
from foobar.enums import PurchaseStatus
from ..factories import (
    AccountFactory,
    CardFactory,
    PurchaseFactory,
    PurchaseItemFactory
)
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
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

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
        self.assertEqual(response.data['amount'], 103)
        _, balance = wallet_api.get_balance(wallet_obj.owner_id, 'SEK')
        self.assertEqual(balance, Money(897, 'SEK'))

    def test_cash_purchase(self):
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
            'account_id': None,
            'products': [
                {'id': product_obj1.id, 'qty': 1},
                {'id': product_obj2.id, 'qty': 3},
            ]
        }
        response = self.api_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], 103)

        purchase_id = response.data['id']
        url = reverse('api:purchases-detail', kwargs={'pk': purchase_id})
        data = {'status': 'FINALIZED'}
        response = self.api_client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        _, balance = wallet_api.get_balance(settings.FOOBAR_CASH_WALLET, 'SEK')
        self.assertEqual(balance, Money(103, 'SEK'))

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

    def test_list_purchases(self):
        purchase_obj1 = PurchaseFactory.create()
        purchase_obj2 = PurchaseFactory.create(account=purchase_obj1.account)
        card_obj = CardFactory.create(account=purchase_obj1.account)
        product_obj1 = ProductFactory.create(
            name='Billys Original',
            price=Money(13, 'SEK')
        )
        product_obj2 = ProductFactory.create(
            name='Kebabrulle',
            price=Money(30, 'SEK')
        )
        PurchaseItemFactory.create(
            purchase=purchase_obj1,
            product_id=product_obj1.pk,
            amount=product_obj1.price
        )
        PurchaseItemFactory.create(
            purchase=purchase_obj2,
            product_id=product_obj2.pk,
            amount=product_obj2.price
        )
        url = reverse('api:purchases-list')
        query_params = {'card_id': card_obj.number}
        response = self.api_client.get(url, query_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_purchase(self):
        purchase_obj = PurchaseFactory.create()
        product_obj1 = ProductFactory.create(
            name='Billys Original',
            price=Money(13, 'SEK')
        )
        product_obj2 = ProductFactory.create(
            name='Kebabrulle',
            price=Money(30, 'SEK')
        )
        PurchaseItemFactory.create(
            purchase=purchase_obj,
            product_id=product_obj1.pk,
            amount=product_obj1.price
        )
        PurchaseItemFactory.create(
            purchase=purchase_obj,
            product_id=product_obj2.pk,
            amount=product_obj2.price
        )

        url = reverse('api:purchases-detail', kwargs={'pk': purchase_obj.pk})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('items', [])), 2)

        # Try retrieve a nonexisting purchase
        url = reverse('api:purchases-detail', kwargs={'pk': str(uuid.uuid4())})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_finalize_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

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
        response = self.api_client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        purchase_id = response.data['id']
        url = reverse('api:purchases-detail', kwargs={'pk': purchase_id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], PurchaseStatus.PENDING.value)

        data = {'status': 'FINALIZED'}
        response = self.api_client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        url = reverse('api:purchases-detail', kwargs={'pk': purchase_id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'],
                         PurchaseStatus.FINALIZED.value)

        # Try finalizing a nonexisting purchase
        url = reverse('api:purchases-detail', kwargs={'pk': str(uuid.uuid4())})
        response = self.api_client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_purchase(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

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
        response = self.api_client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        purchase_id = response.data['id']
        url = reverse('api:purchases-detail', kwargs={'pk': purchase_id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], PurchaseStatus.PENDING.value)

        data = {'status': 'CANCELED'}
        response = self.api_client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        url = reverse('api:purchases-detail', kwargs={'pk': purchase_id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'],
                         PurchaseStatus.CANCELED.value)

    def test_update_purchase_to_invalid_status(self):
        account_obj = AccountFactory.create()
        wallet_obj = WalletFactory.create(owner_id=account_obj.id)
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1000, 'SEK')
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

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
        response = self.api_client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        purchase_id = response.data['id']
        url = reverse('api:purchases-detail', kwargs={'pk': purchase_id})

        data = {'status': 'PENDING'}
        response = self.api_client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'status': 'NOTASTATUS'}
        response = self.api_client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
