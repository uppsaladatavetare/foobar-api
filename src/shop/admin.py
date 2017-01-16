from django.contrib import admin
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from . import models, api


class ProductStateFilter(admin.SimpleListFilter):
    title = _('Product state')
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        return (
            ('unassociated', _('Unassociated products')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'unassociated':
            return queryset.filter(product=None)
        return queryset


@admin.register(models.SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'sku', 'product',)
    list_filter = (ProductStateFilter, 'supplier',)
    search_fields = ('name', 'sku',)
    raw_id_fields = ('product',)

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


class DeliveryItemInline(admin.TabularInline):
    fields = ('supplier_product', 'is_associated', 'qty', 'price',
              'total_price',)
    readonly_fields = ('total_price', 'is_associated',)
    ordering = ('-supplier_product__product',)
    verbose_name = _('Delivery item')
    model = models.Delivery.items.through
    raw_id_fields = ('supplier_product',)
    extra = 0

    def is_associated(self, obj):
        # Ugly hack for forcing django admin to display the value as a boolean
        return obj.is_associated
    is_associated.boolean = True

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('supplier_product', 'qty', 'price',)
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return not obj.locked if obj is not None else True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('supplier_product',
                                 'supplier_product__product')


@admin.register(models.Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'total_amount', 'date_created',)
    list_filter = ('supplier',)
    inlines = (DeliveryItemInline,)
    readonly_fields = ('total_amount', 'date_created', 'valid',
                       'error_message', 'locked',)
    actions_on_top = True
    fieldsets = (
        (None, {
            'fields': (
                'supplier',
                'report',
                'date_created',
             )
        }),
        (_('Additional info'), {
            'fields': (
                'total_amount',
                'locked',
                ('valid', 'error_message',)
            )
        }),

    )

    class Media:
        css = {
            'all': (
                'css/hide_admin_original.css',
            )
        }

    def valid(self, obj):
        return obj.valid
    valid.boolean = True

    def error_message(self, obj):
        if not obj.valid:
            return _('Some of the products need to be associated.')
        return '---'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('supplier', 'report',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        super(DeliveryAdmin, self).save_model(request, obj, form, change)
        if not change:
            api.populate_delivery(obj.id)

    def process_delivery(self, request, obj_id):
        from django.shortcuts import get_object_or_404
        from django.contrib import messages
        from django.http import HttpResponseRedirect, Http404
        obj = get_object_or_404(models.Delivery, id=obj_id)
        if obj.locked:
            raise Http404()
        elif not obj.valid:
            self.message_user(request, self.error_message(obj), messages.ERROR)
        else:
            api.process_delivery(obj.id)
            msg = _('The inventory has been updated accordingly.')
            self.message_user(request, msg)
        url = reverse(
            'admin:shop_delivery_change',
            args=[obj_id],
            current_app=self.admin_site.name,
        )
        return HttpResponseRedirect(url)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r'^(?P<obj_id>.+)/process/$',
                self.admin_site.admin_view(self.process_delivery),
                name='delivery-process',
            ),
        ]
        return custom_urls + urls


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
    max_num = 1
    extra = 1
    min_num = 1

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
