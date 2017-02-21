import jwt

from django.conf import settings
from django.utils import timezone
from rest_framework import parsers, renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CardTokenSerializer


class ObtainFooCardToken(APIView):
    parser_classes = (
        parsers.FormParser,
        parsers.MultiPartParser,
        parsers.JSONParser
    )
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = CardTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.validated_data['account']

        expiration_date = timezone.now() + timezone.timedelta(minutes=5)
        token = jwt.encode(
            {'exp': expiration_date, 'account_id': str(account.pk)},
            settings.SECRET_WEBTOKEN,
            algorithm='HS256'
        )

        return Response({'card_token': token.decode()})


obtain_foocard_token = ObtainFooCardToken.as_view()
