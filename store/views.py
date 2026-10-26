from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Product, ProductVariant, Coupon
from core.models import Banner
from .category_catalog import category_tree


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
    # Only top-level categories for homepage display
    categories = category_tree()
    return render(request, "store/home.html", {
        "banners": banners,
        "featured_products": featured,
        "categories": categories,
    })


def product_list(request):
    products = Product.objects.filter(is_active=True).prefetch_related("images").select_related("category")
    categories = category_tree()

    cat_slug = request.GET.get("category")
    sort = request.GET.get("sort", "newest")
    current_category_obj = None

    if cat_slug:
        try:
            current_category_obj = Category.objects.get(slug=cat_slug, is_active=True)
            # Include products from this category AND all its children
            cat_ids = current_category_obj.descendant_ids()
            products = products.filter(category__id__in=cat_ids)
        except Category.DoesNotExist:
            products = products.none()

    if sort == "price_asc":
        products = products.order_by("base_price")
    elif sort == "price_desc":
        products = products.order_by("-base_price")
    else:
        products = products.order_by("-created_at")

    from django.core.paginator import Paginator
    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "store/product_list.html", {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "current_category": cat_slug,
        "current_category_obj": current_category_obj,
        "subcategories": current_category_obj.children.filter(is_active=True, show_in_navigation=True) if current_category_obj else [],
        "page_title": current_category_obj.name if current_category_obj else "All Products",
        "current_sort": sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = product.variants.filter(is_active=True)
    images = product.images.all()
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk).prefetch_related("images")[:4]
    return render(request, "store/product_detail.html", {
        "product": product,
        "variants": variants,
        "images": images,
        "related_products": related,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    # Include products from this category AND all its children
    cat_ids = category.descendant_ids()
    products = Product.objects.filter(category__id__in=cat_ids, is_active=True).prefetch_related("images")

    sort = request.GET.get("sort", "newest")
    if sort == "price_asc":
        products = products.order_by("base_price")
    elif sort == "price_desc":
        products = products.order_by("-base_price")
    else:
        products = products.order_by("-created_at")

    from django.core.paginator import Paginator
    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "store/product_list.html", {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": category_tree(),
        "current_category": slug,
        "current_category_obj": category,
        "subcategories": category.children.filter(is_active=True, show_in_navigation=True),
        "page_title": category.name,
        "current_sort": sort,
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
