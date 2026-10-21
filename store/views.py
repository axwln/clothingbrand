from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Product, ProductVariant, Coupon
from core.models import Banner


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_cart(request):
    return request.session.setdefault("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


# ── Storefront views ──────────────────────────────────────────────────────────

def home(request):
    banners = Banner.objects.filter(is_active=True)
    featured = Product.objects.filter(is_active=True, is_featured=True).prefetch_related("images")[:8]
    categories = Category.objects.filter(is_active=True)
    return render(request, "store/home.html", {
        "banners": banners,
        "featured_products": featured,
        "categories": categories,
    })


def product_list(request):
    products = Product.objects.filter(is_active=True).prefetch_related("images").select_related("category")
    categories = Category.objects.filter(is_active=True)

    cat_slug = request.GET.get("category")
    sort = request.GET.get("sort", "newest")

    if cat_slug:
        products = products.filter(category__slug=cat_slug)

    if sort == "price_asc":
        products = products.order_by("base_price")
    elif sort == "price_desc":
        products = products.order_by("-base_price")
    else:
        products = products.order_by("-created_at")

    return render(request, "store/product_list.html", {
        "products": products,
        "categories": categories,
        "current_category": cat_slug,
        "current_sort": sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = product.variants.filter(is_active=True)
    images = product.images.all()
    return render(request, "store/product_detail.html", {
        "product": product,
        "variants": variants,
        "images": images,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True).prefetch_related("images")
    return render(request, "store/product_list.html", {
        "products": products,
        "categories": Category.objects.filter(is_active=True),
        "current_category": slug,
        "page_title": category.name,
    })


def search(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.none()
    if q:
        products = Product.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q),
            is_active=True
        ).prefetch_related("images")
    return render(request, "store/search.html", {"products": products, "query": q})


# ── Cart views ────────────────────────────────────────────────────────────────

def cart_add(request, variant_id):
    if request.method != "POST":
        return redirect("store:cart_detail")
    variant = get_object_or_404(ProductVariant, pk=variant_id, is_active=True)
    qty = max(1, int(request.POST.get("quantity", 1)))
    cart = _get_cart(request)
    key = str(variant_id)
    current_qty = cart.get(key, {}).get("quantity", 0)
    new_qty = current_qty + qty
    if new_qty > variant.stock:
        new_qty = variant.stock
    cart[key] = {"quantity": new_qty}
    _save_cart(request, cart)
    return redirect("store:cart_detail")


def cart_update(request, variant_id):
    if request.method != "POST":
        return redirect("store:cart_detail")
    variant = get_object_or_404(ProductVariant, pk=variant_id, is_active=True)
    qty = int(request.POST.get("quantity", 1))
    cart = _get_cart(request)
    key = str(variant_id)
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = {"quantity": min(qty, variant.stock)}
    _save_cart(request, cart)
    return redirect("store:cart_detail")


def cart_remove(request, variant_id):
    cart = _get_cart(request)
    cart.pop(str(variant_id), None)
    _save_cart(request, cart)
    return redirect("store:cart_detail")


def cart_detail(request):
    cart = _get_cart(request)
    items = []
    subtotal = 0
    for variant_id, data in list(cart.items()):
        try:
            variant = ProductVariant.objects.select_related("product").get(pk=int(variant_id), is_active=True)
        except ProductVariant.DoesNotExist:
            cart.pop(variant_id)
            continue
        price = variant.product.effective_price
        qty = data["quantity"]
        line = price * qty
        subtotal += line
        items.append({"variant": variant, "quantity": qty, "price": price, "line_total": line})
    _save_cart(request, cart)
    return render(request, "store/cart.html", {"cart_items": items, "subtotal": subtotal})


# ── Static pages ──────────────────────────────────────────────────────────────

def about(request):
    return render(request, "store/about.html")


def contact(request):
    return render(request, "store/contact.html")


def policy(request, page):
    return render(request, "store/policy.html", {"page": page})
