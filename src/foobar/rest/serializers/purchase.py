from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from utils.exceptions import InvalidTransition
from foobar.enums import PurchaseStatus
from shop import api as shop_api
from ..fields import MoneyField, IntEnumField
from utils.enums import validate_transition


class PurchaseRequestSerializer(serializers.Serializer):
    account_id = serializers.UUIDField(allow_null=True)
    products = serializers.ListField(allow_empty=False)

    def validate_products(self, value):
        for product in value:
            if 'id' not in product or 'qty' not in product:
                raise serializers.ValidationError(
                    _('Each product must contain "id" and "qty".')
                )
            product_obj = shop_api.get_product(product['id'])
            if product_obj is None:
                raise serializers.ValidationError(
                    _('Product with id "{}" not found.'.format(product['id']))
                )
            if product['qty'] <= 0:
                raise serializers.ValidationError(
                    _('Product quantity must be greater than 0.')
                )
        return value

    def as_purchase_kwargs(self):
        products = [(p['id'], p['qty'])
                    for p in self.validated_data['products']]
        return {
            'account_id': self.validated_data['account_id'],
            'products': products
        }


class PurchaseItemSerializer(serializers.Serializer):
    qty = serializers.IntegerField()
    product_id = serializers.CharField()


class PurchaseSerializer(serializers.Serializer):
    """Serializes a purchase, as retrieved from the foobar API call:
        `get_purchase()`
    """
    id = serializers.UUIDField(allow_null=False)
    amount = MoneyField()
    status = IntEnumField()

    def to_representation(self, instance):
        purchase, items = instance
        purchase_obj = super().to_representation(purchase)
        item_serializer = PurchaseItemSerializer(items, many=True)
        purchase_obj['items'] = item_serializer.data
        return purchase_obj


class PurchaseStatusSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=False)

    def validate_status(self, value):
        if value.upper() not in PurchaseStatus.members():
            raise serializers.ValidationError(
                _('Status named: {} not found.'.format(value))
            )
        try:
            purchase_obj = self.context.get('purchase')
            validate_transition(
                PurchaseStatus,
                from_state=purchase_obj.status,
                to_state=getattr(PurchaseStatus, value)
            )
        except InvalidTransition:
            msg = _('Illegal updating existing purchase to a {} status'.format(
                value
            ))
            raise serializers.ValidationError(msg)
        return value

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return getattr(PurchaseStatus, data.get('status', ''))
