import tempfile
from django import forms
from django.shortcuts import get_object_or_404
from django.contrib import admin, messages
from django.http import HttpResponseRedirect, Http404
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from .suppliers.base import SupplierAPIException
from . import models, api, exceptions


class ReadonlyMixin:
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StocktakeItemInline(ReadonlyMixin, admin.TabularInline):
    model = models.StocktakeItem
    fields = ('product', 'category', 'qty',)
    readonly_fields = ('product', 'category',)
    ordering = ('product__category', 'product__name',)
    extra = 0

    def category(self, obj):
        return obj.product.category

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.locked:
            return self.readonly_fields + ('qty',)
        return self.readonly_fields


@admin.register(models.StocktakeChunk)
class StocktakeChunkAdmin(ReadonlyMixin, admin.ModelAdmin):
    inlines = [StocktakeItemInline]
    fields = ('parent_link', 'locked', 'owner',)
    readonly_fields = fields

    class Media:
        css = {'all': ('css/hide_admin_original.css',)}

    def response_change(self, request, obj):
        if '_lock' in request.POST:
            if obj.owner != request.user and not request.user.is_superuser:
                self.message_user(
                    request=request,
                    message=_('You cannot lock a chunk you do not own.'),
                    level=messages.ERROR
                )
                return HttpResponseRedirect(
                    reverse('admin:shop_stocktakechunk_change',
                            args=(obj.id,))
                )
            try:
                api.finalize_stocktake_chunk(obj.id)
            except exceptions.APIException as e:
                self.message_user(
                    request=request,
                    message=str(e),
                    level=messages.ERROR
                )
                return HttpResponseRedirect(
                    reverse('admin:shop_stocktakechunk_change',
                            args=(obj.id,))
                )
            new_chunk = api.assign_free_stocktake_chunk(
                request.user.id, obj.stocktake_id
            )
            if new_chunk is None:
                self.message_user(request, _('No chunks left to work on.'))
                return HttpResponseRedirect(
                    reverse('admin:shop_stocktake_change',
                            args=(obj.stocktake.id,))
                )
            return HttpResponseRedirect(
                reverse('admin:shop_stocktakechunk_change',
                        args=(new_chunk.id,))
            )
        return super().response_change(request, obj)

    def parent_link(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse('admin:shop_stocktake_change', args=(obj.stocktake_id,)),
            obj.id
        )
    parent_link.allow_tags = True
    parent_link.verbose_name = _('Parent')

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class StocktakeChunkInline(ReadonlyMixin, admin.TabularInline):
    model = models.StocktakeChunk
    fields = ('link', 'locked', 'owner',)
    readonly_fields = fields
    extra = 0

    def link(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse('admin:shop_stocktakechunk_change', args=(obj.id,)),
            obj.id
        )
    link.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Stocktake)
class StocktakeAdmin(ReadonlyMixin, admin.ModelAdmin):
    list_display = ('id', 'locked', 'date_created',)
    fields = ('id', 'locked', 'progress',)
    readonly_fields = ('id', 'locked', 'progress',)
    inlines = [StocktakeChunkInline]
    actions = None

    class Media:
        css = {'all': ('css/hide_admin_original.css',)}

    def progress(self, obj=None):
        if obj:
            return '{0:.0f}%'.format(obj.progress * 100)

    def response_change(self, request, obj):
        if '_finalize' in request.POST:
            api.finalize_stocktaking(obj.id)
        return super().response_change(request, obj)

    def has_delete_permission(self, request, obj=None):
        return obj and not obj.locked

    def initiate_stocktaking(self, request):
        try:
            obj = api.initiate_stocktaking()
        except exceptions.APIException as e:
            self.message_user(request, str(e), messages.ERROR)
        url = reverse('admin:shop_stocktake_change', args=(obj.id,))
        return HttpResponseRedirect(url)

    def assign_free_chunk(self, request, obj_id):
        chunk_obj = api.assign_free_stocktake_chunk(request.user.id, obj_id)
        if not chunk_obj:
            self.message_user(request, _('No chunks left to work on.'))
            return HttpResponseRedirect(
                reverse('admin:shop_stocktake_change',
                        args=(chunk_obj.stocktake.id,))
            )
        return HttpResponseRedirect(
            reverse('admin:shop_stocktakechunk_change', args=(chunk_obj.id,))
        )

    def finalize_stocktaking(self, request, obj_id):
        try:
            obj = api.finalize_stocktaking(obj_id)
        except exceptions.APIException as e:
            self.message_user(request, str(e), messages.ERROR)
            url = reverse('admin:shop_stocktake_changelist')
            return HttpResponseRedirect(url)
        return HttpResponseRedirect(
            reverse('admin:shop_stocktake_change', args=(obj.id,))
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r'^initiate-stocktaking/$',
                self.admin_site.admin_view(self.initiate_stocktaking),
                name='initiate-stocktaking',
            ),
            url(
                r'^(?P<obj_id>.+)/assign-free-chunk/$',
                self.admin_site.admin_view(self.assign_free_chunk),
                name='assign-free-chunk',
            ),
            url(
                r'^(?P<obj_id>.+)/finalize/$',
                self.admin_site.admin_view(self.finalize_stocktaking),
                name='finalize-stocktaking',
            ),
        ]
        return custom_urls + urls


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
    fields = ('received', 'supplier_product', 'category', 'is_associated',
              'qty', 'price', 'total_price',)
    readonly_fields = ('total_price', 'is_associated', 'category',)
    ordering = ('-supplier_product__product__category',
                'supplier_product__product__name', 'received',)
    verbose_name = _('Delivery item')
    model = models.Delivery.items.through
    raw_id_fields = ('supplier_product',)
    extra = 0

    def category(self, obj):
        return obj.supplier_product.product.category.name

    def is_associated(self, obj):
        # Ugly hack for forcing django admin to display the value as a boolean
        return obj.is_associated
    is_associated.boolean = True

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.locked:
            return self.readonly_fields + ('supplier_product', 'qty', 'price',
                                           'received',)
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return not obj.locked if obj is not None else True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('supplier_product',
                                 'supplier_product__product',
                                 'supplier_product__product__category',)


class DeliveryForm(forms.ModelForm):
    """Implements custom validation for the Delivery admin."""

    def clean(self):
        supplier = self.cleaned_data.get('supplier')
        report = self.cleaned_data.get('report')
        if report is not None and supplier is not None:
            try:
                # `report` contain most likely an in-memory file.
                # Save it to a temporary file, then try to parse it.
                with tempfile.NamedTemporaryFile() as f:
                    f.write(report.read())
                    items = api.parse_report(supplier.internal_name, f.name)
            except SupplierAPIException as e:
                raise forms.ValidationError(
                    _('Report parse error: %s') % str(e)
                )
            if not items:
                raise forms.ValidationError(
                    _('No products could be imported from the report file.')
                )
        return self.cleaned_data


@admin.register(models.Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'total_amount', 'locked',
                    'date_created',)
    list_filter = ('supplier', 'locked',)
    inlines = (DeliveryItemInline,)
    readonly_fields = ('total_amount', 'date_created', 'valid',
                       'error_message', 'locked',)
    ordering = ('-date_created',)
    actions = None
    form = DeliveryForm
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
        if not obj.associated:
            return _('Some of the products need to be associated.')
        if not obj.received:
            return _('Some of the products need to be marked as received.')
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

    def has_delete_permission(self, request, obj=None):
        # Disable deleting of processed deliveries
        if obj:
            return not obj.locked
        return super().has_delete_permission(request, obj)


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
    ordering = ('name',)
    inlines = (ProductTransactionCreatorInline,)
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
