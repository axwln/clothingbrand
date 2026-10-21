from django.utils import timezone
from django.db import models
from decimal import Decimal


def get_effective_price(product):
    """Return the lowest valid price for a product considering sale price and active offers."""
    price = product.sale_price if product.sale_price else product.base_price
    now = timezone.now()
    from .models import Offer
    all_offers = Offer.objects.filter(
        is_active=True, start_date__lte=now, end_date__gte=now
    ).filter(
        models.Q(applies_to_all=True) |
        models.Q(products=product) |
        models.Q(categories=product.category)
    ).distinct()

    for offer in all_offers:
        if offer.discount_type == "percent":
            discounted = product.base_price * (1 - offer.discount_value / Decimal("100"))
        else:
            discounted = product.base_price - offer.discount_value
        discounted = max(discounted, Decimal("0"))
        price = min(price, discounted)

    return price
