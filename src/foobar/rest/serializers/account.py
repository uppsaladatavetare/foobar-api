from rest_framework import serializers
from foobar.wallet import api as wallet_api
from ..fields import MoneyField
from django.core import signing


class AccountSerializer(serializers.Serializer):
    def get_balance(self, instance):
        _, balance = wallet_api.get_balance(instance.id)
        return MoneyField().to_representation(balance)

    def get_token(self, instance):
        token = signing.dumps({'id': str(instance.id)})
        return token

    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True, source='user.id')
    name = serializers.CharField(read_only=True)
    balance = serializers.SerializerMethodField()
    token = serializers.SerializerMethodField()
    is_complete = serializers.BooleanField(read_only=True)


class AccountQuerySerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
