from rest_framework import serializers
from foobar.wallet import api as wallet_api

from ..fields import MoneyField, IntEnumField


class WalletSerializer(serializers.Serializer):
    def get_balance(self, instance):
        _, balance = wallet_api.get_balance(instance.owner_id)
        return MoneyField().to_representation(balance)

    id = serializers.UUIDField(read_only=True)
    owner_id = serializers.UUIDField(read_only=True)
    balance = serializers.SerializerMethodField()


class NewWalletTrxSerializer(serializers.Serializer):
    amount = MoneyField()
    reference = serializers.CharField()


class WalletTrxSerializer(NewWalletTrxSerializer):
    trx_type = IntEnumField()


class WalletTrxParamsSerializer(serializers.Serializer):
    owner_id = serializers.UUIDField()


class WalletDepositSerializer(serializers.Serializer):
    owner_id = serializers.UUIDField()
    amount = MoneyField(non_negative=True)
    reference = serializers.CharField(required=False)


class WalletWithdrawalSerializer(WalletDepositSerializer):
    pass
