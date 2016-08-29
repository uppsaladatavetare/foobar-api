from django.contrib import admin


class ScannerWidget(admin.widgets.AdminTextInputWidget):
    """Widget providing access to the scanner accessories (rfid & barcode)"""
    def __init__(self, *args, **kwargs):
        self.scanner = kwargs.pop('scanner', None)
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        button = '''<ul class="object-tools inline-object-tools"><li>
            <a href="#" class="grp-state-focus ladda-button scan-btn">
                <span class="ladda-label">Scan a {}</span>
            </a>
        </li></ul>
        '''.format(self.scanner[:-1])
        return super().render(name, value, attrs=None) + button
