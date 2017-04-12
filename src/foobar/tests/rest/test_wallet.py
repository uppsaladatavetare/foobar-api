import uuid
from decimal import Decimal
from django.core.urlresolvers import reverse_lazy as reverse
from rest_framework import status
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet import enums
from foobar.wallet import Money
from foobar.rest.fields import MoneyField
from .base import AuthenticatedAPITestCase


def serialize_money(x):
    return MoneyField().to_representation(x)


class TestWalletAPI(AuthenticatedAPITestCase):

    def setUp(self):
        super().setUp()
        self.force_authenticate()

    def test_retrieve_existing(self):
        # retrieve an existing wallet
        wallet_obj = WalletFactory.create()
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(100)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        owner_id = wallet_obj.owner_id
        url = reverse('api:wallets-detail', kwargs={'pk': owner_id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], Decimal('100'))

    def test_retrieve_non_existing(self):
        # retrieve a non-existing wallet (should create one)
        owner_id = uuid.uuid4()
        url = reverse('api:wallets-detail', kwargs={'pk': owner_id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], Decimal('0'))

    def test_deposit(self):
        owner_id = uuid.uuid4()
        url = reverse('api:wallets-deposit', kwargs={'pk': owner_id})
        response = self.api_client.post(url, data={
            'owner_id': owner_id,
            'amount': serialize_money(Money(50)),
            'reference': '123'
        })
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('api:wallets-detail', kwargs={'pk': owner_id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], Decimal('50'))
        # test with a negative amount
        url = reverse('api:wallets-deposit', kwargs={'pk': owner_id})
        response = self.api_client.post(url, data={
            'owner_id': owner_id,
            'amount': serialize_money(Money(-10)),
            'reference': '321'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # test
        url = reverse('api:wallets-deposit', kwargs={'pk': owner_id})
        response = self.api_client.post(url, data={
            'owner_id': owner_id,
            'amount': serialize_money(Money(-10)),
            'reference': '321'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_withdraw(self):
        # make the money rain first
        wallet_obj = WalletFactory.create()
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(10000)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        owner_id = wallet_obj.owner_id
        url = reverse('api:wallets-withdraw', kwargs={'pk': owner_id})
        response = self.api_client.post(url, data={
            'owner_id': owner_id,
            'amount': serialize_money(Money(5050)),
            'reference': '123'
        })
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('api:wallets-detail', kwargs={'pk': owner_id})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], Decimal('4950'))
        # test with a negative amount
        url = reverse('api:wallets-withdraw', kwargs={'pk': owner_id})
        response = self.api_client.post(url, data={
            'owner_id': owner_id,
            'amount': serialize_money(Money(-10)),
            'reference': '321'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # test withdrawing more money than what is left in the wallet
        url = reverse('api:wallets-withdraw', kwargs={'pk': owner_id})
        response = self.api_client.post(url, data={
            'owner_id': owner_id,
            'amount': serialize_money(Money(10000)),
            'reference': '444'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestWalletTrxAPI(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.force_authenticate()

    def test_list(self):
        wallet_obj = WalletFactory.create()
        trx_obj = WalletTrxFactory(
            wallet=wallet_obj,
            amount=Money(100)
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)

        owner_id = wallet_obj.owner_id
        url = reverse('api:wallet_trxs-list')
        response = self.api_client.get(url, data={'owner_id': owner_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # no owner_id supplied
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
