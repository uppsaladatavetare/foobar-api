from rest_framework import serializers
from shop import api as shop_api


class PurchaseSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    products = serializers.ListField(allow_empty=False)

    def validate_products(self, value):
        for product in value:
            if 'id' not in product or 'qty' not in product:
                raise serializers.ValidationError(
                    'Each product must contain "id" and "qty".'
                )
            product_obj = shop_api.get_product(product['id'])
            if product_obj is None:
                raise serializers.ValidationError(
                    'Product with id "{}" not found.'.format(product['id'])
                )
            if product['qty'] <= 0:
                raise serializers.ValidationError(
                    'Product quantity must be greater than 0.'
                )
        return value

    def as_purchase_kwargs(self):
        products = [(p['id'], p['qty'])
                    for p in self.validated_data['products']]
        return {
            'account_id': self.validated_data['account_id'],
            'products': products
        }
