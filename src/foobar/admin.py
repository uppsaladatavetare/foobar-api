from django.contrib import admin
from foobar.wallet import api as wallet_api
from shop import api as shop_api
from . import models


class ReadOnlyMixin(object):
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class PurchaseInline(ReadOnlyMixin, admin.TabularInline):
    model = models.Purchase
    fields = ('id', 'date_created', 'amount',)
    readonly_fields = ('id', 'date_created', 'amount')
    ordering = ('-date_created',)


class PurchaseItemInline(ReadOnlyMixin, admin.TabularInline):
    model = models.PurchaseItem
    fields = ('product_name', 'product_ean', 'qty', 'amount',)
    readonly_fields = ('product_name', 'product_ean', 'qty', 'amount',)

    def product_name(self, obj):
        obj = shop_api.get_product(obj.product_id)
        if obj:
            return obj.name

    def product_ean(self, obj):
        obj = shop_api.get_product(obj.product_id)
        if obj:
            return obj.code


@admin.register(models.Account)
class AccountAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'card_id', 'balance')
    readonly_fields = ('id', 'balance', 'date_created', 'date_modified')
    inlines = (PurchaseInline,)
    fieldsets = (
        (None, {
            'fields': (
                'id',
                'user',
                'card_id',
            )
        }),
        ('Additional information', {
            'fields': (
                'balance',
                'date_created',
                'date_modified',
            )
        })
    )

    def balance(self, obj):
        _, balance = wallet_api.get_balance(obj.id)
        return balance


@admin.register(models.Purchase)
class PurchaseAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'account', 'amount', 'date_created',)
    readonly_fields = ('id', 'account', 'amount', 'date_created',
                       'date_modified')
    inlines = (PurchaseItemInline,)
