from django.core.management.base import BaseCommand
import shop.api


class Command(BaseCommand):
    def handle(self, *args, **options):
        products = shop.api.list_products()
        for product in products:
            shop.api.update_out_of_stock_forecast(product.id)
