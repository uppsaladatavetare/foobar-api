from django.conf import settings
from django.db import transaction
from .models import Account, Purchase, PurchaseItem
from foobar.wallet import api as wallet_api
from shop import api as shop_api
from shop import enums as shop_enums
from moneyed import Money


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
        shop_api.create_product_transaction(
            product_id=product_obj.id,
            trx_type=shop_enums.TrxType.PURCHASE,
            qty=-qty
        )
        PurchaseItem.objects.create(
            purchase=purchase_obj,
            product_id=product_obj.id,
            qty=qty,
            amount=product_obj.price
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
