from rest_framework import serializers
from ..fields import MoneyField


class ProductSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    code = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    image = serializers.ImageField(allow_null=True)
    price = MoneyField(non_negative=True)
    category = serializers.UUIDField(read_only=True, source='category.id')
    active = serializers.BooleanField(default=False)
    qty = serializers.IntegerField(read_only=True)


class ProductParamSerializer(serializers.Serializer):
    start = serializers.IntegerField(min_value=0, required=False)
    limit = serializers.IntegerField(min_value=0, required=False)
    code = serializers.CharField(required=False)


class ProductCategorySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    image = serializers.ImageField(allow_null=True)
