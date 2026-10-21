from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from store.models import Category, Product, ProductVariant, Offer, Coupon


def make_category(name="Dresses"):
    return Category.objects.create(name=name, slug=name.lower())


def make_product(category, name="Test Dress", price="2000.00"):
    return Product.objects.create(
        category=category, name=name, slug=name.lower().replace(" ", "-"),
        base_price=Decimal(price), is_active=True,
    )


def make_variant(product, size="M", stock=10):
    return ProductVariant.objects.create(
        product=product, sku=f"SKU-{product.pk}-{size}", size=size, stock=stock
    )


class ProductModelTest(TestCase):
    def setUp(self):
        self.cat = make_category()
        self.product = make_product(self.cat)

    def test_effective_price_no_offer(self):
        self.assertEqual(self.product.effective_price, Decimal("2000.00"))

    def test_effective_price_with_sale_price(self):
        self.product.sale_price = Decimal("1500.00")
        self.product.save()
        self.assertEqual(self.product.effective_price, Decimal("1500.00"))

    def test_effective_price_with_active_offer(self):
        now = timezone.now()
        offer = Offer.objects.create(
            name="20% off",
            discount_type="percent",
            discount_value=Decimal("20"),
            applies_to_all=True,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            is_active=True,
        )
        self.assertEqual(self.product.effective_price, Decimal("1600.00"))

    def test_effective_price_expired_offer_ignored(self):
        now = timezone.now()
        Offer.objects.create(
            name="Expired",
            discount_type="percent",
            discount_value=Decimal("50"),
            applies_to_all=True,
            start_date=now - timedelta(days=2),
            end_date=now - timedelta(days=1),
            is_active=True,
        )
        self.assertEqual(self.product.effective_price, Decimal("2000.00"))

    def test_discount_percent(self):
        self.product.sale_price = Decimal("1600.00")
        self.product.save()
        self.assertEqual(self.product.discount_percent, 20)

    def test_slug_auto_generated(self):
        p = Product.objects.create(
            category=self.cat, name="New Dress", base_price=Decimal("1000")
        )
        self.assertEqual(p.slug, "new-dress")


class CartViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = make_category()
        self.product = make_product(self.cat)
        self.variant = make_variant(self.product)

    def test_add_to_cart(self):
        response = self.client.post(
            f"/cart/add/{self.variant.pk}/", {"quantity": 2}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        cart = self.client.session.get("cart", {})
        self.assertIn(str(self.variant.pk), cart)
        self.assertEqual(cart[str(self.variant.pk)]["quantity"], 2)

    def test_add_to_cart_respects_stock(self):
        self.client.post(f"/cart/add/{self.variant.pk}/", {"quantity": 999})
        cart = self.client.session.get("cart", {})
        self.assertEqual(cart[str(self.variant.pk)]["quantity"], self.variant.stock)

    def test_remove_from_cart(self):
        self.client.post(f"/cart/add/{self.variant.pk}/", {"quantity": 1})
        self.client.post(f"/cart/remove/{self.variant.pk}/")
        cart = self.client.session.get("cart", {})
        self.assertNotIn(str(self.variant.pk), cart)

    def test_cart_page_loads(self):
        response = self.client.get("/cart/")
        self.assertEqual(response.status_code, 200)


class ProductListViewTest(TestCase):
    def setUp(self):
        self.cat = make_category()
        make_product(self.cat, "Dress A")
        make_product(self.cat, "Dress B")

    def test_product_list_loads(self):
        response = self.client.get("/products/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dress A")

    def test_category_filter(self):
        cat2 = make_category("Tops")
        make_product(cat2, "Top X")
        response = self.client.get(f"/products/?category={cat2.slug}")
        self.assertContains(response, "Top X")
        self.assertNotContains(response, "Dress A")

    def test_search(self):
        response = self.client.get("/search/?q=Dress")
        self.assertContains(response, "Dress A")

    def test_search_no_results(self):
        response = self.client.get("/search/?q=xyz123")
        self.assertContains(response, "No results")
