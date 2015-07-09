import os
import binascii
from bitfield import BitField
from django.db import models
from django.conf import settings


class Token(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    scopes = BitField(flags=settings.API_TOKEN_SCOPES)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode('utf8')

    def __str__(self):
        return self.key
