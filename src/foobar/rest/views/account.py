from rest_framework import viewsets, status
from rest_framework.response import Response
from authtoken.permissions import HasTokenScope

import foobar.api

from ..serializers.account import AccountSerializer


class AccountAPI(viewsets.ViewSet):
    permission_classes = (HasTokenScope('accounts'),)

    def retrieve(self, request, pk):
        account_obj = foobar.api.get_account(card_id=pk)
        serializer = AccountSerializer(account_obj)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )
