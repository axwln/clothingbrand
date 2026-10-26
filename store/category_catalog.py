from django.db.models import Count, Q
from .models import Category


def category_tree():
    categories = list(Category.objects.filter(is_active=True).annotate(
        direct_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('order', 'name', 'pk'))
    by_parent = {}
    for category in categories:
        by_parent.setdefault(category.parent_id, []).append(category)

    def build(category, seen):
        if category.pk in seen:
            return None
        category.nav_children = []
        category.product_count = category.direct_count
        for child in by_parent.get(category.pk, []):
            child = build(child, seen | {category.pk})
            if child:
                category.product_count += child.product_count
                if child.show_in_navigation:
                    category.nav_children.append(child)
        return category

    return [build(c, set()) for c in by_parent.get(None, []) if c.show_in_navigation]
