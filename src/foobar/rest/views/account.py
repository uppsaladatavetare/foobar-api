from rest_framework import viewsets, status
from rest_framework.response import Response
from authtoken.permissions import HasTokenScope


import foobar.api

from ..serializers.account import AccountQuerySerializer, AccountSerializer


class AccountAPI(viewsets.ViewSet):
    permission_classes = (HasTokenScope('accounts'),)

    def retrieve(self, request, pk):
        serializer = AccountQuerySerializer(data={'card_id': pk})
        serializer.is_valid(raise_exception=True)
        account_obj = foobar.api.get_account_by_card(card_id=pk)
        if account_obj is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = AccountSerializer(account_obj)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )
