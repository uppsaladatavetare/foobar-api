from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from . import models


@admin.register(models.ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    pass


class ProductTransactionViewerInline(admin.TabularInline):
    model = models.ProductTransaction
    fields = ('qty', 'trx_type', 'date_created',)
    readonly_fields = ('qty', 'trx_type', 'date_created',)
    ordering = ('-date_created',)
    verbose_name = _('View transaction')
    verbose_name_plural = _('View transactions')
    max_num = 25

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ProductTransactionCreatorInline(admin.TabularInline):
    model = models.ProductTransaction
    fields = ('qty', 'trx_type',)
    verbose_name = _('Add transaction')
    verbose_name_plural = _('Add transaction')
    max_num = 1

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.none()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'qty', 'price', 'active',)
    list_filter = ('active', 'category',)
    search_fields = ('code', 'name',)
    readonly_fields = ('qty', 'date_created', 'date_modified',)
    inlines = (
        ProductTransactionCreatorInline,
        ProductTransactionViewerInline,
    )
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'code',
                'description',
                'category',
                'image',
                'price',
                'active',
            )
        }),
        ('Additional information', {
            'fields': (
                'qty',
                'date_created',
                'date_modified',
            )
        }),
    )

    class Media:
        css = {
            'all': (
                'css/hide_admin_original.css',
                'css/scan_card.css',
                'css/ladda-themeless.min.css',
            )
        }
        js = (
            'js/spin.min.js',
            'js/ladda.min.js',
            'js/sock.js',
            'js/thunderpush.js',
            'js/scan-card.js',
        )
