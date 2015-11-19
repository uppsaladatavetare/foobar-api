from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from .models import Account, Purchase, PurchaseItem
from foobar.wallet import api as wallet_api
from shop import api as shop_api
from shop import enums as shop_enums
from moneyed import Money
from .exceptions import NotCancelableException
from . import enums


def get_account(card_id):
    obj, _ = Account.objects.get_or_create(
        card_id=card_id
    )
    return obj


@transaction.atomic
def purchase(account_id, products):
    """
    Products should be a list of tuples containing paiars of product ids
    and their quantities. If account_id is None, a cash purchase will be made -
    no account will be assigned to the purchase and the money will be
    transfered to the cash wallet.
    """
    if account_id is not None:
        account_obj = Account.objects.get(id=account_id)
    else:
        account_obj = None
    purchase_obj = Purchase.objects.create(account=account_obj)
    products = [(shop_api.get_product(p), q) for p, q in products]
    # make sure the quantites are greater than 0
    assert all(q > 0 for _, q in products)
    # make sure that all the products exist
    assert all(p is not None for p, q in products)
    for product_obj, qty in products:
        trx_obj = PurchaseItem.objects.create(
            purchase=purchase_obj,
            product_id=product_obj.id,
            qty=qty,
            amount=product_obj.price
        )
        shop_api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=shop_enums.TrxType.PURCHASE,
            qty=-qty,
            reference=trx_obj
        )
    zero_money = Money(0, settings.DEFAULT_CURRENCY)
    total_amount = sum((p.price * q for p, q in products), zero_money)
    if account_id is not None:
        wallet_api.transfer(
            debtor_id=account_obj.id,
            creditor_id=settings.FOOBAR_MAIN_WALLET,
            amount=total_amount,
            reference=purchase_obj.id
        )
    else:
        wallet_api.deposit(
            owner_id=settings.FOOBAR_CASH_WALLET,
            amount=total_amount,
            reference=purchase_obj.id
        )
    return purchase_obj


def get_purchase(purchase_id):
    """Returns a purchase together with the purhcased items in it."""
    try:
        purchase_obj = Purchase.objects.get(id=purchase_id)
        return purchase_obj, purchase_obj.items.all()
    except Purchase.DoesNotExist:
        return None


@transaction.atomic
def cancel_purchase(purchase_id, force=False):
    purchase_obj = Purchase.objects.get(id=purchase_id)
    if not force and not purchase_obj.deletable:
        raise NotCancelableException(_('The purchase cannot be canceled.'))
    assert purchase_obj.status == enums.PurchaseStatus.FINALIZED
    purchase_obj.status = enums.PurchaseStatus.CANCELED
    purchase_obj.save()
    # Cancel related shop item transactions
    for item_trx_obj in purchase_obj.items.all():
        trx_objs = shop_api.get_product_transactions_by_ref(item_trx_obj.id)
        # Only one transaction with given reference should exist
        assert len(trx_objs) == 1
        shop_api.cancel_product_transaction(trx_objs[0].id)
    # Cancel related wallet transactions
    trx_objs = wallet_api.get_transactions_by_ref(purchase_obj.id)
    # Exactly two transactions (withdrawal + deposit) with given reference
    # should exist for card payments. Only one for cash payments.
    assert ((purchase_obj.account is not None and len(trx_objs) == 2)
            or purchase_obj.account is None and len(trx_objs) == 1)
    for trx_obj in trx_objs:
        wallet_api.cancel_transaction(trx_obj.id)


def list_purchases(account_id, start=None, stop=None, **kwargs):
    """Returns a list of purchases for given criteria.

    Together with each purchase, a list of purchased items is returned.
    """

    account_obj = Account.objects.get(id=account_id)
    purchase_objs = account_obj.purchases.filter(
        account_id=account_id,
        **kwargs
    )[start:stop]
    return [get_purchase(obj.id) for obj in purchase_objs]
