import decimal
from unittest import mock
from os.path import join, dirname, abspath
from django.test import TestCase
from ..suppliers import get_supplier_api, narlivs
from ..suppliers.base import SupplierAPIException

TESTDATA_DIR = join(dirname(abspath(__file__)), 'data')


class NarlivsTest(TestCase):
    def report_path(self, name):
        return join(TESTDATA_DIR, name)

    def test_pdf_to_text(self):
        text = narlivs.pdf_to_text(self.report_path('delivery_report.pdf'))
        self.assertTrue('001337' in text)

    def test_receive_missing_delivery(self):
        # Let's parse a missing file
        with self.assertRaises(SupplierAPIException):
            api = get_supplier_api('narlivs')
            api.parse_delivery_report('404notfound')

    def test_receive_invalid_delivery(self):
        # Let's parse a file with invalid format
        with mock.patch('shop.suppliers.narlivs.pdf_to_text') as m:
            api = get_supplier_api('narlivs')
            m.return_value = 'bacon'
            with self.assertRaises(SupplierAPIException):
                api.parse_delivery_report('404notfound')

    def test_receive_delivery(self):
        api = get_supplier_api('narlivs')
        path = self.report_path('delivery_report.pdf')
        items = api.parse_delivery_report(path)
        self.assertEqual(len(items), 32)
        for item in items:
            self.assertEqual(len(item.sku), 9)

    @mock.patch('narlivs.Narlivs.get_product')
    def test_retrieve_product(self, mock_narlivs):
        m = mock_narlivs.return_value = mock.MagicMock()
        m.data = {
            'name': 'GOOD KEBABA',
            'price': decimal.Decimal('13.37'),
            'units': 2
        }
        api = get_supplier_api('narlivs')
        product = api.retrieve_product('1337')
        self.assertIsNotNone(product)
        self.assertEqual(product.name, 'Good Kebaba')
        self.assertEqual(product.price, decimal.Decimal('13.37'))
        self.assertEqual(product.units, 2)

        # Let's try now to fetch a missing product
        mock_narlivs.return_value.data = None
        product = api.retrieve_product('1337')
        self.assertIsNone(product)

    @mock.patch('narlivs.Narlivs.get_cart')
    def test_order_product(self, mock_get_cart):
        api = get_supplier_api('narlivs')
        api.order_product('1337', 2)
        mock_get_cart.return_value.add_product.assert_has_calls([
            mock.call('1337'),
            mock.call('1337')
        ])

    def test_receive_delivery2(self):
        api = get_supplier_api('narlivs')
        path = self.report_path('delivery_report2.pdf')
        items = api.parse_delivery_report(path)
        self.assertEqual(len(items), 41)
        for item in items:
            self.assertEqual(len(item.sku), 9)
