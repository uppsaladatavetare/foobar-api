import os
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from bananas.models import TimeStampedModel, UUIDModel
from moneyed import Money
from enumfields import EnumIntegerField
from djmoney.models.fields import MoneyField
from utils.models import ScannerField
from . import enums, querysets


class OverwriteFileSystemStorage(FileSystemStorage):
    def _save(self, name, content):
        self.delete(name)
        return super()._save(name, content)

    def get_available_name(self, name, max_length=None):
        return name


def generate_product_filename(instance, filename):
    _, ext = os.path.splitext(filename)
    return 'product/{code}{ext}'.format(ext=ext, code=instance.code)


def generate_supplier_product_filename(instance, filename):
    _, ext = os.path.splitext(filename)
    return 'supplier/{supplier}/{sku}{ext}'.format(
        supplier=instance.supplier.id,
        sku=instance.sku,
        ext=ext,
    )


def generate_delivery_report_filename(instance, filename):
    _, ext = os.path.splitext(filename)
    return 'report/{delivery_id}{ext}'.format(
        delivery_id=instance.id,
        ext=ext,
    )


class Supplier(UUIDModel):
    name = models.CharField(max_length=32)
    internal_name = models.CharField(max_length=32)

    class Meta:
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')

    def __str__(self):
        return '{0.name}'.format(self)


class SupplierProduct(UUIDModel, TimeStampedModel):
    """Holds product information provided by the supplier."""
    supplier = models.ForeignKey('Supplier', related_name='products')
    product = models.ForeignKey('Product', related_name='supplier_products',
                                null=True, blank=True)
    name = models.CharField(max_length=64)
    sku = models.CharField(max_length=32, verbose_name=_('SKU'))
    price = MoneyField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY,
        currency_choices=settings.CURRENCY_CHOICES
    )
    image = models.ImageField(blank=True, null=True,
                              upload_to=generate_supplier_product_filename,
                              storage=OverwriteFileSystemStorage())

    class Meta:
        verbose_name = _('supplier product')
        verbose_name_plural = _('supplier products')
        unique_together = ('supplier', 'sku',)

    def __str__(self):
        return '{0.supplier.name}: {0.name}'.format(self)


class Delivery(UUIDModel, TimeStampedModel):
    """Represents the set of products delivered to the shop by a supplier."""
    supplier = models.ForeignKey('Supplier', related_name='deliveries')
    items = models.ManyToManyField('SupplierProduct', through='DeliveryItem')
    report = models.FileField(upload_to=generate_delivery_report_filename,
                              storage=OverwriteFileSystemStorage())
    locked = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Delivery')
        verbose_name_plural = _('Deliveries')

    @property
    def valid(self):
        """Tells whether the delivery is valid for processing or not.

        In order to process a delivery, all the delivery items must be
        associated with a product in the system.
        """
        qs = self.items.all().select_related('product')
        return not any(item.product is None for item in qs)

    @property
    def total_amount(self):
        items = self.delivery_items.all()
        if not items:
            return None
        currency = items[0].price_currency
        zero_money = Money(0, currency)
        return sum((item.total_price for item in items.all()), zero_money)

    def __str__(self):
        fmt = 'Delivery from {0.supplier.name} ({0.date_created:%Y-%m-%m})'
        return fmt.format(self)


class DeliveryItem(UUIDModel):
    delivery = models.ForeignKey('Delivery', on_delete=models.CASCADE,
                                 related_name='delivery_items')
    supplier_product = models.ForeignKey('SupplierProduct',
                                         on_delete=models.PROTECT,
                                         related_name='delivery_item')
    qty = models.PositiveIntegerField()
    price = MoneyField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY,
        currency_choices=settings.CURRENCY_CHOICES
    )

    @property
    def is_associated(self):
        return self.supplier_product.product is not None

    @property
    def total_price(self):
        try:
            return self.qty * self.price
        except TypeError:
            return None


class ProductCategory(UUIDModel):
    """Groups together similar products."""
    name = models.CharField(max_length=64)
    image = models.ImageField(blank=True, null=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return '{0.name}'.format(self)


class Product(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=64)
    code = ScannerField(scanner='products', max_length=13, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True,
                              upload_to=generate_product_filename,
                              storage=OverwriteFileSystemStorage())
    category = models.ForeignKey(ProductCategory, blank=True, null=True)
    # TODO: make sure that the price cannot be negative
    price = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency=settings.DEFAULT_CURRENCY,
        currency_choices=settings.CURRENCY_CHOICES
    )
    active = models.BooleanField(default=True)

    # cached quantity
    qty = models.IntegerField(default=0)
    objects = querysets.ProductQuerySet.as_manager()

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def __str__(self):
        return '{0.name}'.format(self)


class ProductTransaction(UUIDModel, TimeStampedModel):
    product = models.ForeignKey(Product, related_name='transactions')
    qty = models.IntegerField()
    trx_type = EnumIntegerField(enums.TrxType)
    trx_status = EnumIntegerField(enums.TrxStatus,
                                  default=enums.TrxStatus.FINALIZED)
    reference_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     null=True, blank=True)
    reference_id = models.UUIDField(default=uuid.uuid4, null=True, blank=True)
    reference = GenericForeignKey('reference_ct', 'reference_id')
    objects = querysets.ProductTrxQuerySet.as_manager()

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    def __str__(self):
        return '{0.product.name} {0.trx_type} {0.qty}'.format(self)
