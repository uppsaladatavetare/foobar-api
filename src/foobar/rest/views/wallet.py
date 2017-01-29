from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from authtoken.permissions import HasTokenScope

from foobar.wallet import api as wallet_api
from wallet.exceptions import InsufficientFunds

from ..serializers.wallet import (
    WalletSerializer,
    WalletTrxSerializer,
    WalletTrxParamsSerializer,
    WalletDepositSerializer,
    WalletWithdrawalSerializer,
)


class WalletAPI(viewsets.ViewSet):
    """Handles wallets and all the operations the can be performed on them.

    Wallets are retrieved only using the owner_id. The actual
    pk is for the internal use.
    """
    permission_classes = (HasTokenScope('wallets'),)

    def retrieve(self, request, pk):
        """Retrieves wallet details."""
        wallet_obj = wallet_api.get_wallet(pk)
        serializer = WalletSerializer(wallet_obj)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @detail_route(methods=['POST'])
    def deposit(self, request, pk):
        """Deposits money into a wallet.

        amount_
        """
        owner_serializer = WalletTrxParamsSerializer(data={'owner_id': pk})
        owner_serializer.is_valid(raise_exception=True)
        deposit_serializer = WalletDepositSerializer(data=request.POST)
        deposit_serializer.is_valid(raise_exception=True)
        wallet_api.deposit(
            owner_serializer.validated_data['owner_id'],
            deposit_serializer.validated_data['amount'],
            deposit_serializer.validated_data['reference']
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['POST'])
    def withdraw(self, request, pk):
        """Withdraws money from a wallet."""
        owner_serializer = WalletTrxParamsSerializer(data={'owner_id': pk})
        owner_serializer.is_valid(raise_exception=True)
        withdrawal_serializer = WalletWithdrawalSerializer(data=request.POST)
        withdrawal_serializer.is_valid(raise_exception=True)
        try:
            wallet_api.withdraw(
                owner_serializer.validated_data['owner_id'],
                withdrawal_serializer.validated_data['amount'],
                withdrawal_serializer.validated_data['reference']
            )
        except InsufficientFunds:
            # TODO: move this to serializer? think about possible
            # race conditions
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WalletTrxAPI(viewsets.ViewSet):
    permission_classes = (HasTokenScope('wallet_trxs'),)

    def list(self, request):
        """Retrieves all the transactions for given wallet."""
        serializer = WalletTrxParamsSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        owner_id = serializer.validated_data['owner_id']
        trxs = wallet_api.list_transactions(owner_id)
        serializer = WalletTrxSerializer(trxs, many=True)
        return Response(serializer.data)
