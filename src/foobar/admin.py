from django.contrib import admin
from django.core.urlresolvers import reverse
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
    fields = ('link', 'date_created', 'amount',)
    readonly_fields = ('link', 'date_created', 'amount')
    ordering = ('-date_created',)
    show_change_link = True

    def link(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse('admin:foobar_purchase_change', args=(obj.id,)),
            obj.id
        )
    link.allow_tags = True


class PurchaseItemInline(ReadOnlyMixin, admin.TabularInline):
    model = models.PurchaseItem
    fields = ('link', 'product_ean', 'qty', 'amount',)
    readonly_fields = ('link', 'product_ean', 'qty', 'amount',)

    def product_name(self, obj):
        obj = shop_api.get_product(obj.product_id)
        if obj:
            return obj.name

    def product_ean(self, obj):
        obj = shop_api.get_product(obj.product_id)
        if obj:
            return obj.code

    def link(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse('admin:shop_product_change', args=(obj.product_id,)),
            self.product_name(obj)
        )
    link.allow_tags = True


@admin.register(models.Account)
class AccountAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'card_id', 'balance')
    readonly_fields = ('id', 'wallet_link', 'date_created', 'date_modified')
    inlines = (PurchaseInline,)
    fieldsets = (
        (None, {
            'fields': (
                'id',
                'user',
                'name',
                'card_id',
            )
        }),
        ('Additional information', {
            'fields': (
                'wallet_link',
                'date_created',
                'date_modified',
            )
        })
    )

    class Media:
        css = {'all': ('css/hide_admin_original.css',)}

    def balance(self, obj):
        _, balance = wallet_api.get_balance(obj.id)
        return balance

    def wallet_link(self, obj):
        wallet_obj = wallet_api.get_wallet(obj.id)
        return '<a href="{}">{}</a>'.format(
            reverse('admin:wallet_wallet_change', args=(wallet_obj.id,)),
            self.balance(obj)
        )
    wallet_link.allow_tags = True


@admin.register(models.Purchase)
class PurchaseAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('id', 'account', 'amount', 'date_created',)
    readonly_fields = ('id', 'account', 'amount', 'date_created',
                       'date_modified')
    inlines = (PurchaseItemInline,)

    class Media:
        css = {'all': ('css/hide_admin_original.css',)}
