from importlib import import_module


def get_supplier_api(internal_name):
    """Provides supplier API for the supplier with given internal name."""
    name = '.{}'.format(internal_name)
    return import_module(name, __name__).SupplierAPI()
