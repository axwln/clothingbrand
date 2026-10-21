from django.contrib import admin
from .models import StoreSettings, Banner


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Brand", {"fields": ["brand_name", "logo", "tagline"]}),
        ("Content", {"fields": ["about_text"]}),
        ("Contact", {"fields": ["contact_email", "contact_phone", "address", "whatsapp_number"]}),
        ("Social", {"fields": ["instagram_url"]}),
        ("Policies", {"fields": ["privacy_policy", "shipping_policy", "returns_policy", "terms"]}),
    ]

    def has_add_permission(self, request):
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["title", "order", "is_active"]
    list_editable = ["order", "is_active"]
