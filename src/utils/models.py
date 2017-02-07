from functools import partial
from django.db import models
from . import forms


class ScannerField(models.CharField):
    def __init__(self, *args, **kwargs):
        self.scanner = kwargs.pop('scanner', None)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        field_cls = partial(forms.ScannerField, scanner=self.scanner)
        defaults = {
            'form_class': field_cls
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
