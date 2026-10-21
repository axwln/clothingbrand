from django.contrib import admin
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product_name", "variant_sku", "size", "color", "unit_price", "quantity", "line_total"]
    can_delete = False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ["razorpay_order_id", "razorpay_payment_id", "amount", "status", "created_at"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "customer_name", "customer_phone", "total", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["order_number", "customer_name", "customer_email", "customer_phone"]
    readonly_fields = ["order_number", "created_at", "updated_at"]
    inlines = [OrderItemInline, PaymentInline]
