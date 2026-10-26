from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending Payment"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("packed", "Packed"),
        ("shipped", "Shipped"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=300)
    address_line2 = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    coupon_code = models.CharField(max_length=50, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True)
    # Tracking
    courier_name = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["customer_email"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        import random, string
        prefix = "DVK"
        suffix = "".join(random.choices(string.digits, k=8))
        return f"{prefix}{suffix}"


class OrderItem(models.Model):
    """Immutable snapshot of what was ordered — never references live product prices."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # Snapshot fields — preserved even if product is deleted/changed
    product_name = models.CharField(max_length=200)
    variant_sku = models.CharField(max_length=100)
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    # FK kept for reference but nullable so historical data survives deletions
    variant = models.ForeignKey(
        "store.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.order.order_number} – {self.product_name}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("authorized", "Authorized"),
        ("captured", "Captured"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=300, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default="INR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["razorpay_order_id"]),
            models.Index(fields=["razorpay_payment_id"]),
        ]

    def __str__(self):
        return f"{self.order.order_number} – {self.status}"


class OrderStatusHistory(models.Model):
    """Immutable log of every status change for customer-facing tracking timeline."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.order.order_number} → {self.status}"
