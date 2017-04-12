from rest_framework import viewsets, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from authtoken.permissions import HasTokenScope

from foobar import api
from ..serializers.account import AccountQuerySerializer
from ..serializers.purchase import (
    PurchaseSerializer,
    PurchaseStatusSerializer,
    PurchaseRequestSerializer
)
from wallet.exceptions import InsufficientFunds


class PurchaseAPI(viewsets.ViewSet):
    permission_classes = (HasTokenScope('purchases'),)

    def list(self, request):
        serializer = AccountQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        card_id = request.query_params.get('card_id')
        account_obj = api.get_account_by_card(card_id=card_id)
        purchases = api.list_purchases(account_obj.pk)
        serializer = PurchaseSerializer(purchases, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = PurchaseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            purchase_obj = api.create_purchase(
                **serializer.as_purchase_kwargs()
            )

        except InsufficientFunds:
            return Response(
                'Insufficient funds',
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = PurchaseSerializer(purchase_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk):
        """Retrieves an existing purchase"""
        purchase_obj = api.get_purchase(pk)
        if purchase_obj[0] is None:
            raise NotFound

        serializer = PurchaseSerializer(purchase_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk):
        """Updates the status of a purchase(i.e. FINALIZED or CANCELED)"""
        purchase_obj, items = api.get_purchase(pk)
        if purchase_obj is None:
            raise NotFound

        serializer = PurchaseStatusSerializer(
            data=request.data,
            context={'purchase': purchase_obj}
        )
        serializer.is_valid(raise_exception=True)
        api.update_purchase_status(purchase_obj.pk, serializer.validated_data)

        return Response(status=status.HTTP_204_NO_CONTENT)
