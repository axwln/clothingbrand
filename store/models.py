from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    static_image = models.CharField(max_length=255, blank=True, help_text="Optional static category banner path. Uploaded image takes priority.")
    show_in_navigation = models.BooleanField(default=True, help_text="Hide from navigation without deleting the category or changing products.")

    @property
    def banner_url(self):
        if self.image:
            return self.image.url
        if self.static_image:
            from django.templatetags.static import static
            return static(self.static_image)
        return ""

    def descendant_ids(self):
        edges = list(Category.objects.filter(is_active=True).values_list("id", "parent_id"))
        result, pending = {self.pk}, [self.pk]
        while pending:
            current = pending.pop()
            children = [pk for pk, parent in edges if parent == current and pk not in result]
            result.update(children)
            pending.extend(children)
        return result

    def clean(self):
        from django.core.exceptions import ValidationError
        seen = {self.pk} if self.pk else set()
        node = self.parent
        while node:
            if node.pk in seen:
                raise ValidationError({"parent": "Choose a parent outside this category's descendants."})
            seen.add(node.pk)
            node = node.parent

    def get_ancestors(self):
        """Return list of ancestor categories from root to parent."""
        ancestors = []
        node = self.parent
        while node:
            ancestors.insert(0, node)
            node = node.parent
        return ancestors

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Prevent cyclic parent relationships
        if self.parent_id and self.pk:
            ancestor = self.parent
            while ancestor:
                if ancestor.pk == self.pk:
                    raise ValueError("Cyclic category relationship detected.")
                ancestor = ancestor.parent
        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    care_instructions = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        """Return the current selling price after any active offer."""
        from .utils import get_effective_price
        return get_effective_price(self)

    @property
    def discount_percent(self):
        price = self.effective_price
        if price < self.base_price:
            return int((1 - price / self.base_price) * 100)
        return 0

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.product.name} image {self.pk}"


class ProductVariant(models.Model):
    SIZE_CHOICES = [
        ("XS", "XS"), ("S", "S"), ("M", "M"),
        ("L", "L"), ("XL", "XL"), ("XXL", "XXL"),
        ("FREE", "Free Size"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=100, unique=True)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    color = models.CharField(max_length=50, blank=True)
    color_hex = models.CharField(max_length=7, blank=True, help_text="#RRGGBB")
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("product", "size", "color")]
        indexes = [models.Index(fields=["sku"])]

    def __str__(self):
        return f"{self.product.name} – {self.size} / {self.color or 'N/A'}"


class Offer(models.Model):
    DISCOUNT_TYPE_CHOICES = [("percent", "Percentage"), ("fixed", "Fixed Amount")]

    name = models.CharField(max_length=200)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default="percent")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    applies_to_all = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, blank=True)
    products = models.ManyToManyField(Product, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["is_active", "start_date", "end_date"])]

    def __str__(self):
        return self.name


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [("percent", "Percentage"), ("fixed", "Fixed Amount")]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default="percent")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    uses = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class CategoryImportLabel(models.Model):
    """Stable literal source identity; never infer identity from a slug or case."""
    source_label = models.CharField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="source_labels")


class CategorySourceRow(models.Model):
    workbook_name = models.CharField(max_length=255)
    workbook_sha256 = models.CharField(max_length=64)
    sheet_name = models.CharField(max_length=100)
    sheet_row = models.PositiveIntegerField()
    original_excel_row = models.PositiveIntegerField()
    original_label = models.CharField(max_length=200)
    original_description = models.TextField(blank=True)
    label = models.ForeignKey(CategoryImportLabel, on_delete=models.PROTECT, related_name="source_rows")

    class Meta:
        unique_together = [("workbook_sha256", "sheet_name", "sheet_row")]
        ordering = ["original_excel_row"]
