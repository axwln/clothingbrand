from django.db import models


class StoreSettings(models.Model):
    brand_name = models.CharField(max_length=100, default="DEVIKA CLOTHINGS")
    logo = models.ImageField(upload_to="brand/", blank=True)
    tagline = models.CharField(max_length=200, blank=True)
    about_text = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, help_text="Include country code, e.g. 919876543210")
    instagram_url = models.URLField(blank=True)
    privacy_policy = models.TextField(blank=True)
    shipping_policy = models.TextField(blank=True)
    returns_policy = models.TextField(blank=True)
    terms = models.TextField(blank=True)

    class Meta:
        verbose_name = "Store Settings"
        verbose_name_plural = "Store Settings"

    def __str__(self):
        return self.brand_name

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Banner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to="banners/")
    link_url = models.CharField(max_length=300, blank=True)
    link_text = models.CharField(max_length=100, blank=True, default="Shop Now")
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title
