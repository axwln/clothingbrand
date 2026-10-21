import hashlib
import hmac
import json
from decimal import Decimal

import razorpay
from django.conf import settings
from django.db import models, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from store.models import Coupon, ProductVariant
from .models import Order, OrderItem, Payment


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_cart(request):
    return request.session.get("cart", {})


def _build_cart_items(cart):
    """Return list of dicts with variant, qty, price, line_total. Raises ValueError on stock issues."""
    items = []
    for variant_id, data in cart.items():
        variant = ProductVariant.objects.select_related("product").get(
            pk=int(variant_id), is_active=True, product__is_active=True
        )
        qty = data["quantity"]
        if qty > variant.stock:
            raise ValueError(f"Only {variant.stock} units of {variant.product.name} ({variant.size}) available.")
        price = variant.product.effective_price
        items.append({
            "variant": variant,
            "quantity": qty,
            "unit_price": price,
            "line_total": price * qty,
        })
    return items


def _apply_coupon(code, subtotal):
    """Validate coupon and return discount amount. Returns 0 if invalid."""
    try:
        coupon = Coupon.objects.get(code__iexact=code, is_active=True)
    except Coupon.DoesNotExist:
        return Decimal("0"), "Invalid coupon code."
    now = timezone.now()
    if not (coupon.valid_from <= now <= coupon.valid_until):
        return Decimal("0"), "Coupon has expired."
    if coupon.max_uses and coupon.uses >= coupon.max_uses:
        return Decimal("0"), "Coupon usage limit reached."
    if subtotal < coupon.minimum_order:
        return Decimal("0"), f"Minimum order ₹{coupon.minimum_order} required."
    if coupon.discount_type == "percent":
        discount = subtotal * coupon.discount_value / Decimal("100")
    else:
        discount = min(coupon.discount_value, subtotal)
    return discount, None


# ── Views ─────────────────────────────────────────────────────────────────────

def checkout(request):
    cart = _get_cart(request)
    if not cart:
        return redirect("store:cart_detail")

    try:
        items = _build_cart_items(cart)
    except (ProductVariant.DoesNotExist, ValueError) as e:
        return render(request, "orders/checkout.html", {"error": str(e), "cart_items": []})

    subtotal = sum(i["line_total"] for i in items)
    coupon_code = request.session.get("coupon_code", "")
    discount = Decimal("0")
    coupon_error = None
    if coupon_code:
        discount, coupon_error = _apply_coupon(coupon_code, subtotal)
    total = max(subtotal - discount, Decimal("0"))

    return render(request, "orders/checkout.html", {
        "cart_items": items,
        "subtotal": subtotal,
        "discount": discount,
        "coupon_code": coupon_code,
        "coupon_error": coupon_error,
        "total": total,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })


@require_POST
def apply_coupon(request):
    code = request.POST.get("coupon_code", "").strip()
    if code:
        request.session["coupon_code"] = code
    else:
        request.session.pop("coupon_code", None)
    return redirect("orders:checkout")


@require_POST
@transaction.atomic
def payment_create(request):
    """Create a Razorpay order and a local Order record."""
    cart = _get_cart(request)
    if not cart:
        return JsonResponse({"error": "Cart is empty."}, status=400)

    try:
        items = _build_cart_items(cart)
    except (ProductVariant.DoesNotExist, ValueError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    subtotal = sum(i["line_total"] for i in items)
    coupon_code = request.session.get("coupon_code", "")
    discount = Decimal("0")
    if coupon_code:
        discount, _ = _apply_coupon(coupon_code, subtotal)
    total = max(subtotal - discount, Decimal("0"))

    # Validate form fields
    required = ["customer_name", "customer_email", "customer_phone",
                "address_line1", "city", "state", "pincode"]
    data = {f: request.POST.get(f, "").strip() for f in required}
    missing = [f for f in required if not data[f]]
    if missing:
        return JsonResponse({"error": f"Missing fields: {', '.join(missing)}"}, status=400)

    # Reserve stock (select_for_update inside atomic)
    for item in items:
        variant = ProductVariant.objects.select_for_update().get(pk=item["variant"].pk)
        if variant.stock < item["quantity"]:
            return JsonResponse({"error": f"Insufficient stock for {variant.product.name} ({variant.size})."}, status=400)

    # Create Razorpay order
    if not settings.RAZORPAY_KEY_ID or settings.RAZORPAY_KEY_ID.startswith("rzp_test_xxx"):
        return JsonResponse({"error": "Razorpay credentials not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env."}, status=400)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    amount_paise = int(total * 100)
    rz_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,
    })

    # Create local order
    order = Order.objects.create(
        customer_name=data["customer_name"],
        customer_email=data["customer_email"],
        customer_phone=data["customer_phone"],
        address_line1=data["address_line1"],
        address_line2=request.POST.get("address_line2", "").strip(),
        city=data["city"],
        state=data["state"],
        pincode=data["pincode"],
        subtotal=subtotal,
        discount_amount=discount,
        coupon_code=coupon_code,
        total=total,
        status="pending",
    )
    for item in items:
        OrderItem.objects.create(
            order=order,
            variant=item["variant"],
            product_name=item["variant"].product.name,
            variant_sku=item["variant"].sku,
            size=item["variant"].size,
            color=item["variant"].color,
            unit_price=item["unit_price"],
            quantity=item["quantity"],
            line_total=item["line_total"],
        )

    Payment.objects.create(
        order=order,
        razorpay_order_id=rz_order["id"],
        amount=total,
        status="created",
    )

    return JsonResponse({
        "razorpay_order_id": rz_order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "order_number": order.order_number,
        "key_id": settings.RAZORPAY_KEY_ID,
    })


@require_POST
@transaction.atomic
def payment_verify(request):
    """Verify Razorpay signature and mark order paid."""
    rz_order_id = request.POST.get("razorpay_order_id", "")
    rz_payment_id = request.POST.get("razorpay_payment_id", "")
    rz_signature = request.POST.get("razorpay_signature", "")

    try:
        payment = Payment.objects.select_for_update().get(razorpay_order_id=rz_order_id)
    except Payment.DoesNotExist:
        return redirect("store:home")

    # Idempotency: already captured
    if payment.status == "captured":
        return redirect("orders:order_confirmation", order_number=payment.order.order_number)

    # Verify signature
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{rz_order_id}|{rz_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, rz_signature):
        payment.status = "failed"
        payment.save(update_fields=["status", "updated_at"])
        payment.order.status = "cancelled"
        payment.order.save(update_fields=["status", "updated_at"])
        return redirect("orders:checkout")

    # Deduct stock
    for item in payment.order.items.all():
        if item.variant:
            ProductVariant.objects.filter(pk=item.variant.pk).update(
                stock=models.F("stock") - item.quantity
            )

    # Mark paid
    payment.razorpay_payment_id = rz_payment_id
    payment.razorpay_signature = rz_signature
    payment.status = "captured"
    payment.save(update_fields=["razorpay_payment_id", "razorpay_signature", "status", "updated_at"])

    payment.order.status = "paid"
    payment.order.save(update_fields=["status", "updated_at"])

    # Increment coupon usage
    coupon_code = payment.order.coupon_code
    if coupon_code:
        Coupon.objects.filter(code__iexact=coupon_code).update(uses=models.F("uses") + 1)

    # Clear cart and coupon
    request.session.pop("cart", None)
    request.session.pop("coupon_code", None)

    return redirect("orders:order_confirmation", order_number=payment.order.order_number)


@csrf_exempt
@require_POST
def payment_webhook(request):
    """Razorpay webhook — idempotent payment capture handler."""
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not webhook_secret:
        return HttpResponse(status=400)

    signature = request.headers.get("X-Razorpay-Signature", "")
    expected = hmac.new(
        webhook_secret.encode(),
        request.body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return HttpResponse(status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    event = payload.get("event")
    if event != "payment.captured":
        return HttpResponse(status=200)

    rz_payment_id = payload["payload"]["payment"]["entity"]["id"]
    rz_order_id = payload["payload"]["payment"]["entity"]["order_id"]

    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(razorpay_order_id=rz_order_id)
        except Payment.DoesNotExist:
            return HttpResponse(status=200)

        if payment.status == "captured":
            return HttpResponse(status=200)  # idempotent

        for item in payment.order.items.all():
            if item.variant:
                ProductVariant.objects.filter(pk=item.variant.pk).update(
                    stock=models.F("stock") - item.quantity
                )

        payment.razorpay_payment_id = rz_payment_id
        payment.status = "captured"
        payment.save(update_fields=["razorpay_payment_id", "status", "updated_at"])
        payment.order.status = "paid"
        payment.order.save(update_fields=["status", "updated_at"])

    return HttpResponse(status=200)


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    session_orders = request.session.get("confirmed_orders", [])
    if order_number not in session_orders and not request.user.is_staff:
        session_orders.append(order_number)
        request.session["confirmed_orders"] = session_orders

    # Build WhatsApp URL
    from urllib.parse import quote
    from core.models import StoreSettings
    store = StoreSettings.get()
    wa_url = ""
    if store.whatsapp_number:
        lines = [f"Hi, I just placed Order {order.order_number}:"]
        for item in order.items.all():
            color_part = f" / {item.color}" if item.color else ""
            lines.append(f"- {item.product_name} ({item.size}{color_part}) x{item.quantity} = ₹{item.line_total}")
        lines.append(f"Total: ₹{order.total}")
        lines.append(f"Name: {order.customer_name}")
        lines.append(f"Phone: {order.customer_phone}")
        wa_url = f"https://wa.me/{store.whatsapp_number}?text={quote(chr(10).join(lines))}"

    return render(request, "orders/confirmation.html", {"order": order, "whatsapp_url": wa_url})


def order_lookup(request):
    order = None
    error = None
    if request.method == "POST":
        number = request.POST.get("order_number", "").strip().upper()
        phone = request.POST.get("customer_phone", "").strip()
        try:
            order = Order.objects.prefetch_related("items").get(
                order_number=number, customer_phone=phone
            )
        except Order.DoesNotExist:
            error = "No order found with that number and phone."
    return render(request, "orders/lookup.html", {"order": order, "error": error})


def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    confirmed = request.session.get("confirmed_orders", [])
    if order_number not in confirmed and not request.user.is_staff:
        return redirect("orders:order_lookup")
    return render(request, "orders/order_detail.html", {"order": order})
