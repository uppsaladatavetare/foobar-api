from os.path import join, dirname, abspath
from django.test import TestCase
from ..suppliers import get_supplier_api, narlivs

TESTDATA_DIR = join(dirname(abspath(__file__)), 'data')


class NarlivsTest(TestCase):
    def setUp(self):
        self.api = get_supplier_api('narlivs')
        self.report_path = join(TESTDATA_DIR, 'delivery_report.pdf')

    def test_pdf_to_text(self):
        text = narlivs.pdf_to_text(self.report_path)
        self.assertTrue('001337' in text)

    def test_receive_delivery(self):
        items = self.api.parse_delivery_report(self.report_path)
        self.assertEqual(len(items), 32)
        for item in items:
            self.assertEqual(len(item.sku), 9)
