from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps

from store.models import Category, Product, ProductImage, ProductVariant, Offer, Coupon
from orders.models import Order, Payment
from .models import StoreSettings, Banner


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect("core:dashboard_login")
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Auth ──────────────────────────────────────────────────────────────────────

def dashboard_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("core:dashboard_home")
    error = None
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user and user.is_staff:
            login(request, user)
            return redirect(request.GET.get("next", "core:dashboard_home"))
        error = "Invalid credentials or insufficient permissions."
    return render(request, "dashboard/login.html", {"error": error})


@staff_required
def dashboard_logout(request):
    logout(request)
    return redirect("core:dashboard_login")


# ── Overview ──────────────────────────────────────────────────────────────────

@staff_required
def dashboard_home(request):
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today)
    stats = {
        "orders_today": orders_today.count(),
        "revenue_today": orders_today.filter(status="paid").aggregate(t=Sum("total"))["t"] or 0,
        "orders_total": Order.objects.count(),
        "revenue_total": Order.objects.filter(status="paid").aggregate(t=Sum("total"))["t"] or 0,
        "pending_orders": Order.objects.filter(status="pending").count(),
        "low_stock": ProductVariant.objects.filter(stock__lte=5, is_active=True).count(),
    }
    recent_orders = Order.objects.order_by("-created_at")[:10]
    low_stock_variants = ProductVariant.objects.filter(stock__lte=5, is_active=True).select_related("product")[:10]
    return render(request, "dashboard/home.html", {
        "stats": stats,
        "recent_orders": recent_orders,
        "low_stock_variants": low_stock_variants,
    })


# ── Products ──────────────────────────────────────────────────────────────────

@staff_required
def product_list(request):
    qs = Product.objects.select_related("category").order_by("-created_at")
    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/product_list.html", {"page_obj": page, "query": q})


@staff_required
def product_create(request):
    from .forms import ProductForm
    form = ProductForm(request.POST or None)
    if form.is_valid():
        product = form.save()
        messages.success(request, "Product created.")
        return redirect("core:product_edit", pk=product.pk)
    return render(request, "dashboard/product_form.html", {"form": form, "title": "New Product"})


@staff_required
def product_edit(request, pk):
    from .forms import ProductForm
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("core:product_edit", pk=pk)
    return render(request, "dashboard/product_form.html", {"form": form, "product": product, "title": "Edit Product"})


@staff_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.is_active = False
        product.save(update_fields=["is_active"])
        messages.success(request, "Product archived.")
        return redirect("core:product_list")
    return render(request, "dashboard/confirm_delete.html", {"object": product, "type": "product"})


@staff_required
def product_images(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        files = request.FILES.getlist("images")
        allowed = {"image/jpeg", "image/png", "image/webp"}
        for f in files:
            if f.content_type not in allowed:
                messages.error(request, f"Unsupported file type: {f.content_type}")
                continue
            if f.size > 5 * 1024 * 1024:
                messages.error(request, f"File too large: {f.name}")
                continue
            ProductImage.objects.create(product=product, image=f, alt_text=product.name)
        messages.success(request, "Images uploaded.")
        return redirect("core:product_images", pk=pk)
    return render(request, "dashboard/product_images.html", {"product": product})


@staff_required
def product_image_delete(request, pk, img_pk):
    image = get_object_or_404(ProductImage, pk=img_pk, product__pk=pk)
    if request.method == "POST":
        image.image.delete(save=False)
        image.delete()
        messages.success(request, "Image deleted.")
    return redirect("core:product_images", pk=pk)


# ── Categories ────────────────────────────────────────────────────────────────

@staff_required
def category_list(request):
    categories = Category.objects.select_related("parent").annotate(product_count=Count("products"))
    return render(request, "dashboard/category_list.html", {"categories": categories})


@staff_required
def category_create(request):
    from .forms import CategoryForm
    form = CategoryForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect("core:category_list")
    return render(request, "dashboard/category_form.html", {"form": form, "title": "New Category"})


@staff_required
def category_edit(request, pk):
    from .forms import CategoryForm
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if form.is_valid():
        form.save()
        messages.success(request, "Category updated.")
        return redirect("core:category_list")
    return render(request, "dashboard/category_form.html", {"form": form, "title": "Edit Category"})


# ── Variants ──────────────────────────────────────────────────────────────────

@staff_required
def variant_list(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "dashboard/variant_list.html", {"product": product, "variants": product.variants.all()})


@staff_required
def variant_create(request, pk):
    from .forms import VariantForm
    product = get_object_or_404(Product, pk=pk)
    form = VariantForm(request.POST or None)
    if form.is_valid():
        variant = form.save(commit=False)
        variant.product = product
        variant.save()
        messages.success(request, "Variant created.")
        return redirect("core:variant_list", pk=pk)
    return render(request, "dashboard/variant_form.html", {"form": form, "product": product, "title": "New Variant"})


@staff_required
def variant_edit(request, pk):
    from .forms import VariantForm
    variant = get_object_or_404(ProductVariant, pk=pk)
    form = VariantForm(request.POST or None, instance=variant)
    if form.is_valid():
        form.save()
        messages.success(request, "Variant updated.")
        return redirect("core:variant_list", pk=variant.product.pk)
    return render(request, "dashboard/variant_form.html", {"form": form, "product": variant.product, "title": "Edit Variant"})


@staff_required
def variant_delete(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    product_pk = variant.product.pk
    if request.method == "POST":
        variant.is_active = False
        variant.save(update_fields=["is_active"])
        messages.success(request, "Variant deactivated.")
    return redirect("core:variant_list", pk=product_pk)


# ── Offers ────────────────────────────────────────────────────────────────────

@staff_required
def offer_list(request):
    offers = Offer.objects.all().order_by("-start_date")
    return render(request, "dashboard/offer_list.html", {"offers": offers})


@staff_required
def offer_create(request):
    from .forms import OfferForm
    form = OfferForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Offer created.")
        return redirect("core:offer_list")
    return render(request, "dashboard/offer_form.html", {"form": form, "title": "New Offer"})


@staff_required
def offer_edit(request, pk):
    from .forms import OfferForm
    offer = get_object_or_404(Offer, pk=pk)
    form = OfferForm(request.POST or None, instance=offer)
    if form.is_valid():
        form.save()
        messages.success(request, "Offer updated.")
        return redirect("core:offer_list")
    return render(request, "dashboard/offer_form.html", {"form": form, "title": "Edit Offer"})


# ── Coupons ───────────────────────────────────────────────────────────────────

@staff_required
def coupon_list(request):
    coupons = Coupon.objects.all().order_by("-valid_from")
    return render(request, "dashboard/coupon_list.html", {"coupons": coupons})


@staff_required
def coupon_create(request):
    from .forms import CouponForm
    form = CouponForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Coupon created.")
        return redirect("core:coupon_list")
    return render(request, "dashboard/coupon_form.html", {"form": form, "title": "New Coupon"})


@staff_required
def coupon_edit(request, pk):
    from .forms import CouponForm
    coupon = get_object_or_404(Coupon, pk=pk)
    form = CouponForm(request.POST or None, instance=coupon)
    if form.is_valid():
        form.save()
        messages.success(request, "Coupon updated.")
        return redirect("core:coupon_list")
    return render(request, "dashboard/coupon_form.html", {"form": form, "title": "Edit Coupon"})


# ── Orders ────────────────────────────────────────────────────────────────────

@staff_required
def order_list(request):
    qs = Order.objects.order_by("-created_at")
    status = request.GET.get("status", "")
    q = request.GET.get("q", "")
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(order_number__icontains=q) | Q(customer_name__icontains=q) | Q(customer_phone__icontains=q))
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/order_list.html", {
        "page_obj": page,
        "status_choices": Order.STATUS_CHOICES,
        "current_status": status,
        "query": q,
    })


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, "dashboard/order_detail.html", {
        "order": order,
        "status_choices": Order.STATUS_CHOICES,
    })


@staff_required
def order_status_update(request, pk):
    if request.method == "POST":
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get("status")
        valid = [s[0] for s in Order.STATUS_CHOICES]
        if new_status in valid and new_status != order.status:
            old_status = order.status
            order.status = new_status
            order.save(update_fields=["status", "updated_at"])
            from orders.models import OrderStatusHistory
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                note=request.POST.get("note", "").strip(),
            )
            messages.success(request, f"Order status updated to {new_status}.")
    return redirect("core:order_detail", pk=pk)


@staff_required
def order_tracking_update(request, pk):
    if request.method == "POST":
        order = get_object_or_404(Order, pk=pk)
        order.courier_name = request.POST.get("courier_name", "").strip()
        order.tracking_number = request.POST.get("tracking_number", "").strip()
        order.tracking_url = request.POST.get("tracking_url", "").strip()
        est = request.POST.get("estimated_delivery", "").strip()
        if est:
            from datetime import date
            try:
                order.estimated_delivery = date.fromisoformat(est)
            except ValueError:
                pass
        else:
            order.estimated_delivery = None
        order.save(update_fields=["courier_name", "tracking_number", "tracking_url", "estimated_delivery", "updated_at"])
        messages.success(request, "Tracking details updated.")
    return redirect("core:order_detail", pk=pk)


# ── Banners ───────────────────────────────────────────────────────────────────

@staff_required
def banner_list(request):
    banners = Banner.objects.all()
    return render(request, "dashboard/banner_list.html", {"banners": banners})


@staff_required
def banner_create(request):
    from .forms import BannerForm
    form = BannerForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Banner created.")
        return redirect("core:banner_list")
    return render(request, "dashboard/banner_form.html", {"form": form, "title": "New Banner"})


@staff_required
def banner_edit(request, pk):
    from .forms import BannerForm
    banner = get_object_or_404(Banner, pk=pk)
    form = BannerForm(request.POST or None, request.FILES or None, instance=banner)
    if form.is_valid():
        form.save()
        messages.success(request, "Banner updated.")
        return redirect("core:banner_list")
    return render(request, "dashboard/banner_form.html", {"form": form, "title": "Edit Banner"})


@staff_required
def banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == "POST":
        banner.image.delete(save=False)
        banner.delete()
        messages.success(request, "Banner deleted.")
        return redirect("core:banner_list")
    return render(request, "dashboard/confirm_delete.html", {"object": banner, "type": "banner"})


# ── Store Settings ────────────────────────────────────────────────────────────

@staff_required
def store_settings(request):
    from .forms import StoreSettingsForm
    instance = StoreSettings.get()
    form = StoreSettingsForm(request.POST or None, request.FILES or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, "Settings saved.")
        return redirect("core:store_settings")
    return render(request, "dashboard/settings.html", {"form": form})
