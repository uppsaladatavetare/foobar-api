from django import forms
from . import widgets


class ScannerField(forms.CharField):
    widget = widgets.ScannerWidget

    def __init__(self, *args, **kwargs):
        self.scanner = kwargs.pop('scanner')
        kwargs['widget'] = widgets.ScannerWidget(scanner=self.scanner)
        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attr = super().widget_attrs(widget)
        attr['scanner'] = self.scanner
        return attr
