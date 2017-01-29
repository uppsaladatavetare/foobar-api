from rest_framework import viewsets, status
from rest_framework.response import Response
from authtoken.permissions import HasTokenScope

import shop.api

from ..serializers.product import (
    ProductSerializer,
    ProductParamSerializer,
    ProductCategorySerializer
)


class ProductAPI(viewsets.ViewSet):
    permission_classes = (HasTokenScope('products'),)

    def retrieve(self, request, pk):
        product_obj = shop.api.get_product(pk)
        if product_obj is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product_obj)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def list(self, request):
        serializer = ProductParamSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        product_objs = shop.api.list_products(**serializer.validated_data)
        serializer = ProductSerializer(product_objs, many=True)
        return Response(serializer.data)


class ProductCategoryAPI(viewsets.ViewSet):
    permission_classes = (HasTokenScope('categories'),)

    def list(self, request):
        category_objs = shop.api.list_categories()
        serializer = ProductCategorySerializer(category_objs, many=True)
        return Response(serializer.data)
