from django.db import transaction
from . import models, enums


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
    return models.ProductTransaction.objects.filter(reference=reference)


@transaction.atomic
def create_product_transaction(product_id, trx_type, qty, reference=None):
    """
    Create item transaction for given item.

    It automagically takes care of updating the quantity for the product.
    """
    product_obj = models.Product.objects.get(id=product_id)
    trx_obj = product_obj.transactions.create(
        trx_type=trx_type,
        qty=qty,
        reference=reference
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
