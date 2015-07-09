import os
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from bananas.models import TimeStampedModel, UUIDModel
from enumfields import EnumIntegerField
from djmoney.models.fields import MoneyField
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
    code = models.CharField(max_length=13, unique=True)
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

    objects = querysets.ProductQuerySet

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def __str__(self):
        return '{0.name}'.format(self)


class ProductTransaction(UUIDModel, TimeStampedModel):
    product = models.ForeignKey(Product, related_name='transactions')
    qty = models.IntegerField()
    trx_type = EnumIntegerField(enums.TrxType)

    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')

    def __str__(self):
        return '{0.product.name} {0.trx_type} {0.qty}'.format(self)
