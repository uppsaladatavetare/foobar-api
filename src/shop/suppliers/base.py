from abc import ABCMeta, abstractmethod
from collections import namedtuple


DeliveryItem = namedtuple('DeliveryItem', ['sku', 'price', 'qty'])
SupplierProduct = namedtuple('SupplierProduct', ['name', 'price'])


class SupplierAPIException(Exception):
    pass


class SupplierBase(metaclass=ABCMeta):
    """Defines the interface of a supplier module."""

    @abstractmethod
    def parse_delivery_report(self, report_path):
        """Parses a delivery report file and returns the delivered items.

        :param report_path: Path to the report file.
        :type report_path: str
        :rtype: List[DeliveryItem] -- The list of products imported from the
                                      file.
        :raises: SupplierAPIException
        """

    @abstractmethod
    def retrieve_product(self, sku):
        """Retrieve product data for given SKU.

        :param sku: SKU of the product to be retrieved.
        :type sku: str
        :rtype: Union[SupplierProduct, None]
        """
