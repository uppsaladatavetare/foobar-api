from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from foobar.api import get_account


class CardTokenSerializer(serializers.Serializer):
    number = serializers.CharField(required=True, allow_blank=False)

    def validate_number(self, value):
        account = get_account(value)
        if account is None:
            msg = {'number': _('Card is not registered')}
            raise serializers.ValidationError(msg)

        return value
