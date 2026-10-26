from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from store.models import Category, Product, ProductVariant, Coupon
from orders.models import Order, OrderItem, Payment

User = get_user_model()


def make_order(**kwargs):
    defaults = dict(
        customer_name="Test User",
        customer_email="test@example.com",
        customer_phone="9876543210",
        address_line1="123 Test St",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        subtotal=Decimal("2000"),
        total=Decimal("2000"),
    )
    defaults.update(kwargs)
    return Order.objects.create(**defaults)


class OrderModelTest(TestCase):
    def test_order_number_generated(self):
        order = make_order()
        self.assertTrue(order.order_number.startswith("DVK"))
        self.assertEqual(len(order.order_number), 11)

    def test_order_number_unique(self):
        o1 = make_order()
        o2 = make_order()
        self.assertNotEqual(o1.order_number, o2.order_number)


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        cat = Category.objects.create(name="Dresses", slug="dresses")
        product = Product.objects.create(
            category=cat, name="Test Dress", slug="test-dress",
            base_price=Decimal("2000"), is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product, sku="SKU-001", size="M", stock=10
        )

    def test_checkout_redirects_empty_cart(self):
        response = self.client.get("/orders/checkout/")
        self.assertRedirects(response, "/cart/")

    def test_checkout_loads_with_cart(self):
        session = self.client.session
        session["cart"] = {str(self.variant.pk): {"quantity": 1}}
        session.save()
        response = self.client.get("/orders/checkout/")
        self.assertEqual(response.status_code, 200)

    @override_settings(RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="")
    def test_payment_create_requires_razorpay_credentials(self):
        session = self.client.session
        session["cart"] = {str(self.variant.pk): {"quantity": 1}}
        session.save()
        response = self.client.post("/orders/payment/create/", {
            "customer_name": "Test",
            "customer_email": "t@t.com",
            "customer_phone": "9876543210",
            "address_line1": "123 St",
            "city": "Mumbai",
            "state": "MH",
            "pincode": "400001",
        })
        data = response.json()
        # Missing credentials are isolated from developer environment settings
        self.assertIn("error", data)

    def test_order_lookup_with_wrong_details(self):
        response = self.client.post("/orders/lookup/", {
            "order_number": "MSN00000000",
            "customer_phone": "0000000000",
        })
        self.assertContains(response, "No order found")


class PaymentVerifyTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.order = make_order()
        self.payment = Payment.objects.create(
            order=self.order,
            razorpay_order_id="order_test123",
            amount=Decimal("2000"),
            status="created",
        )

    def test_invalid_signature_marks_failed(self):
        response = self.client.post("/orders/payment/verify/", {
            "razorpay_order_id": "order_test123",
            "razorpay_payment_id": "pay_test123",
            "razorpay_signature": "invalidsignature",
        })
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "failed")
        self.assertEqual(self.payment.order.status, "cancelled")

    def test_unknown_order_id_redirects_home(self):
        response = self.client.post("/orders/payment/verify/", {
            "razorpay_order_id": "order_nonexistent",
            "razorpay_payment_id": "pay_x",
            "razorpay_signature": "x",
        })
        self.assertRedirects(response, "/")


class DashboardPermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user("staff", password="pass", is_staff=True)
        self.regular = User.objects.create_user("regular", password="pass", is_staff=False)

    def test_dashboard_requires_staff(self):
        response = self.client.get("/dashboard/")
        self.assertRedirects(response, "/dashboard/login/")

    def test_regular_user_cannot_access_dashboard(self):
        self.client.login(username="regular", password="pass")
        response = self.client.get("/dashboard/")
        self.assertRedirects(response, "/dashboard/login/")

    def test_staff_can_access_dashboard(self):
        self.client.login(username="staff", password="pass")
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_order_list_requires_staff(self):
        response = self.client.get("/dashboard/orders/")
        self.assertRedirects(response, "/dashboard/login/")


class CouponTest(TestCase):
    def setUp(self):
        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="SAVE10",
            discount_type="percent",
            discount_value=Decimal("10"),
            minimum_order=Decimal("500"),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
            is_active=True,
        )

    def test_apply_coupon_valid(self):
        from orders.views import _apply_coupon
        discount, error = _apply_coupon("SAVE10", Decimal("1000"))
        self.assertIsNone(error)
        self.assertEqual(discount, Decimal("100"))

    def test_apply_coupon_below_minimum(self):
        from orders.views import _apply_coupon
        discount, error = _apply_coupon("SAVE10", Decimal("400"))
        self.assertIsNotNone(error)
        self.assertEqual(discount, Decimal("0"))

    def test_apply_coupon_invalid_code(self):
        from orders.views import _apply_coupon
        discount, error = _apply_coupon("BADCODE", Decimal("1000"))
        self.assertIsNotNone(error)
        self.assertEqual(discount, Decimal("0"))

    def test_apply_coupon_expired(self):
        from orders.views import _apply_coupon
        self.coupon.valid_until = timezone.now() - timedelta(days=1)
        self.coupon.save()
        discount, error = _apply_coupon("SAVE10", Decimal("1000"))
        self.assertIsNotNone(error)
