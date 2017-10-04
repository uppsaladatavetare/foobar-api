import re
import decimal
import subprocess
import tempfile

import narlivs

from django.conf import settings

from .base import (
    DeliveryItem,
    SupplierAPIException,
    SupplierBase,
    SupplierProduct
)

ITEM_PATTERN = re.compile(r"""
    \s*?\d+                    # Row
    \s+?(?P<sku>\d{9})         # SKU
    \s+(?P<description>.+?)    # Description
    \s+?\d+                    # Delivered package quantity
    \s+?(?P<unit>\w+)          # Unit
    \s+?(?P<qty>\d+)           # Delivered unit quantity
    \s+(?P<price>[^ ]+)/ST     # Purchase price
    \s+[\d\.-]+                # Recommended price
    \s+[\d\.-]+                # Marginal %
    \s+(?P<net_price>[\d\.]+)  # Net price
    \s+[\d\.]+$                # Reference
""", re.VERBOSE | re.MULTILINE)

NET_VALUE_PATTERN = re.compile("nettobelopp:\s+([\d.]+?)\s+SEK")

ITEM_TYPE_MAPPINGS = {
    'sku': str,
    'description': str,
    'unit': str,
    'qty': int,
    'price': decimal.Decimal,
    'net_price': decimal.Decimal,
}


def pdf_to_text(path):
    """Converts a PDF file to text.

    Depends on the external pdftotext command line tool.
    """
    with tempfile.NamedTemporaryFile(mode='r') as f:
        code = subprocess.call(['pdftotext', '-q', '-layout', path, f.name])
        if code != 0:
            return None
        return f.read()


class SupplierAPI(SupplierBase):
    """Supplier API implementation for Axfood Närlivs."""

    def __init__(self):
        self.narlivs = narlivs.Narlivs(
            username=settings.NARLIVS_USERNAME,
            password=settings.NARLIVS_PASSWORD
        )

    def parse_delivery_report(self, report_path):
        data = pdf_to_text(report_path)

        if not data:
            raise SupplierAPIException('The report is probably not in PDF '
                                       'format.')

        items = [m.groupdict() for m in ITEM_PATTERN.finditer(data)]
        net = NET_VALUE_PATTERN.search(data)

        if not net or not items:
            raise SupplierAPIException('The report could not be parsed.')

        net = net.group(1)

        # Cast the item values to proper types.
        items = [{k: ITEM_TYPE_MAPPINGS[k](v) for k, v in item.items()}
                 for item in items]

        # Delivery report contain also the pant fee. The fee is represented
        # as an item in the report. We want however to merge the fee with
        # the corresponding item (always the item above the pant fee item).
        consolidated_items = []

        for item in items:
            if item['description'].startswith('PANT '):
                prev_item = consolidated_items[-1]

                # For some drinks, the quantity in the report is incorrect
                # and it is not equal to the quantity of the pant. The pant
                # quantity seems however to be always correct, so we
                # set it as the quantity of the drink.
                if prev_item['qty'] != item['qty']:
                    prev_item['qty'] = item['qty']
                    prev_item['price'] = prev_item['net_price'] / item['qty']
                prev_item['net_price'] += item['net_price']
                prev_item['price'] += item['price']

                # Let's make sure that the computed price is correct
                prev_computed_net_price = prev_item['price'] * prev_item['qty']
                prev_computed_net_price = prev_computed_net_price.quantize(
                    decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP
                )
                if prev_item['net_price'] != prev_computed_net_price:
                    msg = ('The computed price and quantity seem to be wrong '
                           'for product with SKU {} (probably a report '
                           'parser issue).')
                    raise SupplierAPIException(msg.format(item['sku']))
            else:
                consolidated_items.append(item)

        # Make sure that we did not miss any item while parsing
        item_sum1 = sum(item['net_price'] for item in consolidated_items)
        item_sum2 = sum(item['price'] * item['qty']
                        for item in consolidated_items)
        net = decimal.Decimal(net)
        assert item_sum1 == item_sum2 == net

        return [
            DeliveryItem(
                sku=item['sku'],
                price=item['price'],
                qty=item['qty']
            ) for item in consolidated_items
        ]

    def retrieve_product(self, sku):
        data = self.narlivs.get_product(sku=sku).data
        if data is not None:
            return SupplierProduct(
                name=data['name'].title(),
                price=data['price'],
                units=data['units']
            )
        return None

    def order_product(self, sku, qty):
        for _ in range(qty):
            self.narlivs.get_cart().add_product(sku)
