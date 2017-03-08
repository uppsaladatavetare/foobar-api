from os.path import join, dirname, abspath
from django.test import TestCase
from ..suppliers import get_supplier_api, narlivs

TESTDATA_DIR = join(dirname(abspath(__file__)), 'data')


class NarlivsTest(TestCase):
    def setUp(self):
        self.api = get_supplier_api('narlivs')

    def report_path(self, name):
        return join(TESTDATA_DIR, name)

    def test_pdf_to_text(self):
        text = narlivs.pdf_to_text(self.report_path('delivery_report.pdf'))
        self.assertTrue('001337' in text)

    def test_receive_delivery(self):
        api = get_supplier_api('narlivs')
        path = self.report_path('delivery_report.pdf')
        items = api.parse_delivery_report(path)
        self.assertEqual(len(items), 32)
        for item in items:
            self.assertEqual(len(item.sku), 9)

    def test_receive_delivery2(self):
        api = get_supplier_api('narlivs')
        path = self.report_path('delivery_report2.pdf')
        items = api.parse_delivery_report(path)
        self.assertEqual(len(items), 41)
        for item in items:
            self.assertEqual(len(item.sku), 9)
