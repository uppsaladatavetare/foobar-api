from unittest import mock

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import exceptions
from . import factories


class SupplierAdminTest(TestCase):
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

    @mock.patch('shop.api.order_refill')
    def test_order(self, mock_order_refill):
        supplier = factories.SupplierFactory()
        sp = factories.SupplierProductFactory(supplier=supplier)
        url = reverse('admin:supplier-order', args=(supplier.id,))

        # Let's try the error handling
        mock_order_refill.side_effect = exceptions.APIException('error')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        response_messages = list(response.context['messages'])
        self.assertEqual(len(response_messages), 1)
        self.assertEqual(response_messages[0].level, messages.ERROR)
        self.assertRedirects(
            response,
            reverse('admin:shop_supplier_change', args=(supplier.id,))
        )

        mock_order_refill.reset_mock()
        mock_order_refill.side_effect = None
        mock_order_refill.return_value = [sp]
        response = self.client.get(url, follow=True)
        mock_order_refill.assert_called_once_with(supplier.id)
        self.assertEqual(response.status_code, 200)
        response_messages = list(response.context['messages'])
        self.assertEqual(len(response_messages), 1)
        self.assertEqual(response_messages[0].level, messages.INFO)
        self.assertRedirects(
            response,
            reverse('admin:shop_supplier_change', args=(supplier.id,))
        )
