from .models import StoreSettings, Banner


def store_settings(request):
    from store.category_catalog import category_tree
    settings = StoreSettings.get()
    return {
        "store": settings,
        "nav_categories": category_tree(),
    }
