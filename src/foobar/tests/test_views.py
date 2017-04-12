from unittest import mock
from moneyed import Money
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from wallet.tests.factories import WalletFactory, WalletTrxFactory
from wallet import enums
from . import factories
from django.core import signing


class FoobarViewTest(TestCase):
    TESTUSER_NAME = 'the_baconator'
    TESTUSER_PASS = '123'

    def setUp(self):
        self.user = User.objects.create_superuser(
            self.TESTUSER_NAME,
            'bacon@foobar.com',
            self.TESTUSER_PASS
        )
        self.client.login(
            username=self.TESTUSER_NAME,
            password=self.TESTUSER_PASS
        )

    @mock.patch('foobar.api.get_account_by_card')
    def test_account_for_card(self, mock_get_account):
        url = reverse('account_for_card', kwargs={'card_id': 1337})
        mock_get_account.return_value = None
        response = self.client.get(url, follow=True)
        self.assertRedirects(
            response,
            reverse('admin:foobar_account_changelist')
        )
        self.assertEqual(len(response.context['messages']), 1)
        account = factories.AccountFactory()
        mock_get_account.return_value = account
        response = self.client.get(url, follow=True)
        self.assertRedirects(
            response,
            reverse('admin:foobar_account_change', args=(account.id,))
        )
        self.assertEqual(len(response.context['messages']), 0)

    @mock.patch('foobar.api.calculate_correction')
    @mock.patch('foobar.api.make_deposit_or_withdrawal')
    def test_wallet_management(self, mock_deposit_withdrawal, mock_correction):
        wallet_obj = WalletFactory.create()
        trx_obj = WalletTrxFactory.create(
            wallet=wallet_obj,
            amount=Money(1200, 'SEK')
        )
        trx_obj.set_status(enums.TrxStatus.PENDING)
        trx_obj.set_status(enums.TrxStatus.FINALIZED)
        url = reverse('wallet_management',
                      kwargs={'obj_id': wallet_obj.owner_id})
        # Test that deposit or withdrawal
        # is not called if balance will get negative
        response = self.client.post(url,
                                    {'deposit_or_withdrawal_1': ['SEK'],
                                     'save_deposit': ['Submit'],
                                     'comment': ['test'],
                                     'deposit_or_withdrawal_0': ['-3000']})
        mock_deposit_withdrawal.assert_not_called()
        # Test that page can be found
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Test that correction form post is correct and
        # calls function with correct params
        self.client.post(url,
                         {'save_correction': ['Submit'],
                          'balance_1': ['SEK'],
                          'comment': ['test'],
                          'balance_0': ['1000']})
        mock_correction.assert_called_with(Money(1000, 'SEK'),
                                           wallet_obj.owner_id,
                                           self.user,
                                           'test')
        # Test that deposit or withdrawal form post is correct and
        # calls fucnction with correct params
        self.client.post(url,
                         {'deposit_or_withdrawal_1': ['SEK'],
                          'save_deposit': ['Submit'],
                          'comment': ['test'],
                          'deposit_or_withdrawal_0': ['100']})
        mock_deposit_withdrawal.assert_called_with(
            Money(100, 'SEK'),
            wallet_obj.owner_id,
            self.user,
            'test')

    @mock.patch('foobar.api.update_account')
    def test_edit_profile(self, mock_update_account):
        account_obj = factories.AccountFactory.create()
        token = signing.dumps({'id': str(account_obj.id)})
        home_url = reverse('profile-home', kwargs={'token': token})
        good_token_url = reverse('profile-edit', kwargs={'token': token})
        bad_token_url = reverse('profile-edit', kwargs={'token': 'bad'})

        # Assert that page can be found
        response = self.client.get(good_token_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(bad_token_url)
        self.assertEqual(response.status_code, 403)

        # Assure update_account not called when url with bad token send POST
        self.client.post(bad_token_url, {
            'name': 'foo',
            'email': 'test@test.com',
            'save_changes': ['Submit']
        })
        mock_update_account.assert_not_called()

        # Assure set_balance is called when token is valid
        response = self.client.post(good_token_url, {
            'name': 'foo',
            'email': 'test@test.com',
            'save_changes': ['Submit']
        })
        mock_update_account.assert_called_with(account_obj.id,
                                               name='foo',
                                               email='test@test.com')
        self.assertRedirects(response, home_url)

        # Delete the account and try to use to token
        account_obj.delete()
        response = self.client.get(bad_token_url)
        self.assertEqual(response.status_code, 403)
