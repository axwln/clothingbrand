from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:variant_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:variant_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:variant_id>/", views.cart_remove, name="cart_remove"),
    path("search/", views.search, name="search"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.policy, {"page": "privacy"}, name="privacy"),
    path("shipping/", views.policy, {"page": "shipping"}, name="shipping"),
    path("returns/", views.policy, {"page": "returns"}, name="returns"),
    path("terms/", views.policy, {"page": "terms"}, name="terms"),
]
