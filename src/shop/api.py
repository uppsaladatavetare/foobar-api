import logging
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from . import models, enums, suppliers

log = logging.getLogger(__name__)


@transaction.atomic
def create_product(code, name):
    """Create an product"""
    product_obj = models.Product(
        code=code,
        name=name
    )
    product_obj.save()
    return product_obj


@transaction.atomic
def update_product(id, **kwargs):
    product_obj = models.Product.objects.get(id=id)
    for k, v in kwargs.items():
        setattr(product_obj, k, v)
    product_obj.save()


def get_product(id):
    """Return item with given id.

    Returns None if the product does not exist.
    """
    try:
        return models.Product.objects.get(id=id)
    except models.Product.DoesNotExist:
        return None


def get_product_transactions_by_ref(reference):
    """Return item transactions with given reference."""
    ct = ContentType.objects.get_for_model(reference)
    return models.ProductTransaction.objects.filter(
        reference_ct=ct,
        reference_id=reference.pk,
    )


@transaction.atomic
def create_product_transaction(product_id, trx_type, qty, reference=None):
    """
    Create item transaction for given item.

    It automagically takes care of updating the quantity for the product.
    """
    product_obj = models.Product.objects.get(id=product_id)
    ct = None
    if reference is not None:
        ct = ContentType.objects.get_for_model(reference)
    trx_obj = product_obj.transactions.create(
        trx_type=trx_type,
        qty=qty,
        reference_ct=ct,
        reference_id=reference.pk if reference is not None else None
    )
    return trx_obj


@transaction.atomic
def cancel_product_transaction(trx_id):
    trx_obj = models.ProductTransaction.objects.get(id=trx_id)
    trx_obj.trx_status = enums.TrxStatus.CANCELED
    trx_obj.save()


def list_products(start=None, limit=None, **kwargs):
    """Returns a list of products matching the criteria.

    Criteria should be passed to the function as keyword arguments.
    Criteria arguments support Django field lookups.
    """
    return models.Product.objects.filter(**kwargs)[start:limit]


def list_categories():
    return models.ProductCategory.objects.all()


@transaction.atomic
def get_supplier_product(supplier_id, sku):
    """Returns supplier product for given SKU.

    If the product does not exist in the local database, fetch it from the
    supplier.
    """
    try:
        return models.SupplierProduct.objects.get(
            supplier_id=supplier_id,
            sku=sku
        )
    except models.SupplierProduct.DoesNotExist:
        pass

    # Product has not been found in the database. Let's fetch it from
    # the supplier.
    supplier_obj = models.Supplier.objects.get(id=supplier_id)
    supplier_api = suppliers.get_supplier_api(supplier_obj.internal_name)
    product_data = supplier_api.retrieve_product(sku)
    if product_data is None:
        log.warning('Product not found (sku: %s, supplier: %s',
                    sku, supplier_id)
        return None
    product_obj = models.SupplierProduct.objects.create(
        supplier_id=supplier_id,
        sku=sku,
        price=product_data.price,
        name=product_data.name
    )
    return product_obj


def parse_report(supplier_internal_name, report_path):
    """Parses a report file and returns parsed items."""
    supplier_api = suppliers.get_supplier_api(supplier_internal_name)
    return supplier_api.parse_delivery_report(report_path)


@transaction.atomic
def populate_delivery(delivery_id):
    """Populates the delivery with products based on the imported report."""
    delivery_obj = models.Delivery.objects.get(id=delivery_id)
    supplier_obj = delivery_obj.supplier
    items = parse_report(supplier_obj.internal_name, delivery_obj.report.path)
    for item in items:
        product_obj = get_supplier_product(supplier_obj.id, item.sku)
        if product_obj is not None:
            models.DeliveryItem.objects.create(
                delivery=delivery_obj,
                supplier_product_id=product_obj.id,
                qty=item.qty * product_obj.qty_multiplier,
                price=item.price / product_obj.qty_multiplier
            )
    return delivery_obj


@transaction.atomic
def process_delivery(delivery_id):
    """Adjusts the stock quantities based on the delivery data."""
    delivery_obj = models.Delivery.objects.get(id=delivery_id)
    assert delivery_obj.valid, ('Some of the delivered items are not '
                                'associated with a product in the system.')
    for item in delivery_obj.delivery_items.all():
        supplier_product = item.supplier_product
        create_product_transaction(
            product_id=supplier_product.product.id,
            trx_type=enums.TrxType.INVENTORY,
            qty=item.qty,
            reference=item
        )
    delivery_obj.locked = True
    delivery_obj.save()
