from django import forms
from store.models import Category, Product, ProductVariant, Offer, Coupon
from .models import StoreSettings, Banner


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "slug", "description", "care_instructions",
                  "base_price", "sale_price", "is_active", "is_featured"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "care_instructions": forms.Textarea(attrs={"rows": 3}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "image", "is_active", "order"]


class VariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["sku", "size", "color", "color_hex", "stock", "is_active"]


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["name", "discount_type", "discount_value", "applies_to_all",
                  "categories", "products", "start_date", "end_date", "is_active"]
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ["code", "discount_type", "discount_value", "minimum_order",
                  "max_uses", "valid_from", "valid_until", "is_active"]
        widgets = {
            "valid_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "valid_until": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ["title", "subtitle", "image", "link_url", "link_text", "order", "is_active"]


class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        fields = ["brand_name", "logo", "tagline", "about_text", "contact_email",
                  "contact_phone", "address", "whatsapp_number", "instagram_url",
                  "privacy_policy", "shipping_policy", "returns_policy", "terms"]
        widgets = {
            "about_text": forms.Textarea(attrs={"rows": 6}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "privacy_policy": forms.Textarea(attrs={"rows": 10}),
            "shipping_policy": forms.Textarea(attrs={"rows": 10}),
            "returns_policy": forms.Textarea(attrs={"rows": 10}),
            "terms": forms.Textarea(attrs={"rows": 10}),
        }
