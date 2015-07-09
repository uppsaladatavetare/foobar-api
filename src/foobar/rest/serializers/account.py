from rest_framework import serializers


class AccountSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True, source='user.id')
