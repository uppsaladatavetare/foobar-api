import shop.api
from django.core.management.base import BaseCommand
from shop.models import SupplierProduct


class Command(BaseCommand):
    def handle(self, *args, **options):
        products = shop.api.list_products()
        products = SupplierProduct.objects.all()
        for product in products:
            print('Updating {}...'.format(product))
            shop.api.get_supplier_product(
                product.supplier.id,
                product.sku,
                refresh=True
            )
