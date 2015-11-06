from rest_framework import serializers
from foobar.wallet import api as wallet_api
from ..fields import MoneyField


class AccountSerializer(serializers.Serializer):
    def get_balance(self, instance):
        _, balance = wallet_api.get_balance(instance.id)
        return MoneyField().to_representation(balance)

    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True, source='user.id')
    name = serializers.CharField(read_only=True)
    balance = serializers.SerializerMethodField()


class AccountQuerySerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
