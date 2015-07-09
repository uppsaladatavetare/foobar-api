import decimal
from rest_framework import serializers
from foobar.wallet import Money


class MoneyField(serializers.Field):
    default_error_messages = {
        'non_negative': 'The amount must be positive.',
        'not_a_number': 'The amount must be a number.'
    }

    def __init__(self, *args, **kwargs):
        self.non_negative = kwargs.pop('non_negative', False)
        return super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        return obj.amount

    def to_internal_value(self, data):
        try:
            obj = Money(data)
        except decimal.InvalidOperation:
            self.fail('not_a_number')
        if obj < Money('0') and self.non_negative:
            self.fail('non_negative')
        return Money(data)


class IntEnumField(serializers.Field):
    """
    The EnumField does not work well with DRF, when using it together
    with IntegerField in a serializer. This field takes care of properly
    converting the EnumField value to an integer.
    """
    default_error_messages = {
        'not_a_number': 'The amount must be a number.'
    }

    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        try:
            return int(data)
        except ValueError:
            self.fail('not_a_number')
