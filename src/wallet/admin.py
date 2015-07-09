from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from wallet import api as wallet_api
from . import models


class ReadOnlyMixin(object):
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class WalletTransactionViewerInline(ReadOnlyMixin, admin.TabularInline):
    model = models.WalletTransaction
    fields = ('id', 'trx_type', 'trx_status', 'amount', 'reference',
              'date_created')
    readonly_fields = ('id', 'trx_type', 'trx_status', 'amount', 'reference',
                       'date_created')
    ordering = ('-date_created',)
    verbose_name = _('View transaction')
    verbose_name_plural = _('View transactions')


class WalletTransactionCreatorInline(admin.TabularInline):
    model = models.WalletTransaction
    fields = ('trx_type', 'trx_status', 'amount', 'reference',)
    max_num = 1
    verbose_name = _('Add transaction')
    verbose_name_plural = _('Add transaction')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.none()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Wallet)
class WalletAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('owner_id', 'balance',)
    readonly_fields = ('owner_id', 'balance',)
    inlines = (
        WalletTransactionCreatorInline,
        WalletTransactionViewerInline,
    )
    fieldsets = (
        (None, {
            'fields': (
                'owner_id',
            )
        }),
        ('Additional information', {
            'fields': (
                'balance',
            )
        })
    )

    def balance(self, obj):
        _, balance = wallet_api.get_balance(obj.owner_id,
                                            settings.DEFAULT_CURRENCY)
        return balance
