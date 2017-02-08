from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
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
    max_num = 25
    readonly_fields = ('id', 'trx_type', 'trx_status', 'amount', 'reference',
                       'date_created')
    ordering = ('-date_created',)
    verbose_name = _('View transaction')
    verbose_name_plural = _('View transactions')


class WalletTransactionCreatorInline(admin.TabularInline):
    model = models.WalletTransaction
    fields = ('trx_type', 'trx_status', 'amount', 'reference',)
    max_num = 1
    verbose_name = _('Add new transaction')
    verbose_name_plural = _('Add new transaction')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.none()

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Wallet)
class WalletAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ('owner_id', '_balance',)
    readonly_fields = ('owner_id', 'balance',)
    inlines = (
        WalletTransactionCreatorInline,
        #WalletTransactionViewerInline,
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

    def _balance(self, obj):
        # An ugly trick to force the Django admin to format the money
        # field properly.
        return obj.balance

    class Media:
        css = {'all': ('css/hide_admin_original.css',)}
