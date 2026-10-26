from django import forms
from store.models import Category, Product, ProductVariant, Offer, Coupon
from .models import StoreSettings, Banner


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, category):
        path = " / ".join(c.name for c in category.get_ancestors() + [category])
        return path + (" (hidden from navigation)" if not category.show_in_navigation else "")


class ProductForm(forms.ModelForm):
    category = CategoryChoiceField(queryset=Category.objects.all().select_related("parent"))
    class Meta:
        model = Product
        fields = ["category", "name", "slug", "description", "care_instructions",
                  "base_price", "sale_price", "is_active", "is_featured"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "care_instructions": forms.Textarea(attrs={"rows": 3}),
        }


class CategoryForm(forms.ModelForm):
    parent = CategoryChoiceField(queryset=Category.objects.all(), required=False)
    class Meta:
        model = Category
        fields = ["parent", "name", "slug", "description", "image", "is_active", "show_in_navigation", "static_image", "order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        excluded = self.instance.descendant_ids() if self.instance.pk else set()
        self.fields["parent"].queryset = Category.objects.exclude(pk__in=excluded)
        self.fields["parent"].required = False
        self.fields["parent"].empty_label = "— Top-level category —"



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
