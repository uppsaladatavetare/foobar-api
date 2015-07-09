import requests
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from shop import api as shop_api

IMAGE_URL = ('http://www.narlivs.se/is-bin/intershop.static/WFS/'
             'Axfood-NWP2-Site/Axfood-NWP2/sv_SE/product/products/'
             'images/{ean}.jpg')


class Command(BaseCommand):
    help = 'Imports product images from narlivs.se'

    def handle(self, *args, **options):
        products = shop_api.list_products()
        for product in products:
            url = IMAGE_URL.format(ean=product.code)
            response = requests.get(url)
            if response.status_code == 200:
                f = SimpleUploadedFile('tmp.jpg', response.content,
                                       'image/jpeg')
                shop_api.update_product(product.id, image=f)
