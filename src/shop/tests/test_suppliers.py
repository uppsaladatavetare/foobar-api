from django.test import TestCase
from .. import suppliers


class SupplierTest(TestCase):
    def test_get_supplier_api(self):
        api = suppliers.get_supplier_api('narlivs')
        self.assertIsNotNone(api)
