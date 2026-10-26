from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Offer, Coupon, CategoryImportLabel, CategorySourceRow


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active", "show_in_navigation", "order"]
    list_editable = ["is_active", "show_in_navigation", "order"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "base_price", "sale_price", "is_active", "is_featured"]
    list_editable = ["is_active", "is_featured"]
    list_filter = ["category", "is_active", "is_featured"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [ProductImageInline, ProductVariantInline]


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ["name", "discount_type", "discount_value", "start_date", "end_date", "is_active"]
    list_editable = ["is_active"]
    filter_horizontal = ["categories", "products"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "discount_value", "uses", "max_uses", "is_active"]
    list_editable = ["is_active"]


@admin.register(CategoryImportLabel)
class CategoryImportLabelAdmin(admin.ModelAdmin):
    list_display = ["source_label", "category"]
    readonly_fields = ["source_label", "category"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CategorySourceRow)
class CategorySourceRowAdmin(admin.ModelAdmin):
    list_display = ["original_excel_row", "original_label", "original_description", "sheet_name"]
    readonly_fields = [f.name for f in CategorySourceRow._meta.fields]
    search_fields = ["original_label", "original_description"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
