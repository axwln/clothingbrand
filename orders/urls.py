from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("payment/create/", views.payment_create, name="payment_create"),
    path("payment/verify/", views.payment_verify, name="payment_verify"),
    path("payment/webhook/", views.payment_webhook, name="payment_webhook"),
    path("confirmation/<str:order_number>/", views.order_confirmation, name="order_confirmation"),
    path("lookup/", views.order_lookup, name="order_lookup"),
    path("history/<str:order_number>/", views.order_detail, name="order_detail"),
]
