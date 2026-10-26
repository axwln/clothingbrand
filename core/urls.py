from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard_home, name="dashboard_home"),
    path("login/", views.dashboard_login, name="dashboard_login"),
    path("logout/", views.dashboard_logout, name="dashboard_logout"),
    # Products
    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:pk>/images/", views.product_images, name="product_images"),
    path("products/<int:pk>/images/<int:img_pk>/delete/", views.product_image_delete, name="product_image_delete"),
    # Categories
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    # Variants
    path("products/<int:pk>/variants/", views.variant_list, name="variant_list"),
    path("products/<int:pk>/variants/create/", views.variant_create, name="variant_create"),
    path("variants/<int:pk>/edit/", views.variant_edit, name="variant_edit"),
    path("variants/<int:pk>/delete/", views.variant_delete, name="variant_delete"),
    # Offers & Coupons
    path("offers/", views.offer_list, name="offer_list"),
    path("offers/create/", views.offer_create, name="offer_create"),
    path("offers/<int:pk>/edit/", views.offer_edit, name="offer_edit"),
    path("coupons/", views.coupon_list, name="coupon_list"),
    path("coupons/create/", views.coupon_create, name="coupon_create"),
    path("coupons/<int:pk>/edit/", views.coupon_edit, name="coupon_edit"),
    # Orders
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/status/", views.order_status_update, name="order_status_update"),
    path("orders/<int:pk>/tracking/", views.order_tracking_update, name="order_tracking_update"),
    # Banners
    path("banners/", views.banner_list, name="banner_list"),
    path("banners/create/", views.banner_create, name="banner_create"),
    path("banners/<int:pk>/edit/", views.banner_edit, name="banner_edit"),
    path("banners/<int:pk>/delete/", views.banner_delete, name="banner_delete"),
    # Settings
    path("settings/", views.store_settings, name="store_settings"),
]
