"""
Attach the downloaded reference images to Banner, Category, and ProductImage records.
Run once: python manage.py seed_images
"""
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from core.models import Banner
from store.models import Category, Product, ProductImage

MEDIA = Path(__file__).resolve().parents[4] / "clothingbrand" / "media"

BANNER = {
    "title": "New Collection",
    "subtitle": "Effortless elegance for the modern woman.",
    "image": MEDIA / "banners/hero.jpg",
    "link_url": "/products/",
    "link_text": "Shop Now",
    "order": 0,
    "is_active": True,
}

CATEGORY_IMAGES = {
    "dresses": MEDIA / "categories/dresses.jpg",
    "tops":    MEDIA / "categories/tops.jpg",
    "co-ords": MEDIA / "categories/coords.jpg",
}

PRODUCT_IMAGES = {
    "ivory-linen-midi-dress": MEDIA / "products/ivory-linen-midi-dress.jpg",
    "espresso-wrap-dress":    MEDIA / "products/espresso-wrap-dress.jpg",
    "sand-silk-blouse":       MEDIA / "products/sand-silk-blouse.jpg",
}


class Command(BaseCommand):
    help = "Seed reference images for banner, categories, and products"

    def handle(self, *args, **options):
        self._seed_banner()
        self._seed_categories()
        self._seed_products()
        self.stdout.write(self.style.SUCCESS("Images seeded successfully."))

    def _seed_banner(self):
        if Banner.objects.exists():
            self.stdout.write("Banner already exists — skipping.")
            return
        path = BANNER.pop("image")
        banner = Banner(**BANNER)
        with open(path, "rb") as f:
            banner.image.save(path.name, File(f), save=True)
        self.stdout.write(f"  Created banner: {banner.title}")

    def _seed_categories(self):
        for slug, img_path in CATEGORY_IMAGES.items():
            try:
                cat = Category.objects.get(slug=slug)
            except Category.DoesNotExist:
                self.stdout.write(f"  Category '{slug}' not found — skipping.")
                continue
            if cat.image:
                self.stdout.write(f"  Category '{slug}' already has image — skipping.")
                continue
            with open(img_path, "rb") as f:
                cat.image.save(img_path.name, File(f), save=True)
            self.stdout.write(f"  Set image for category: {cat.name}")

    def _seed_products(self):
        for slug, img_path in PRODUCT_IMAGES.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(f"  Product '{slug}' not found — skipping.")
                continue
            if ProductImage.objects.filter(product=product).exists():
                self.stdout.write(f"  Product '{slug}' already has images — skipping.")
                continue
            pi = ProductImage(product=product, is_primary=True, alt_text=product.name)
            with open(img_path, "rb") as f:
                pi.image.save(img_path.name, File(f), save=True)
            self.stdout.write(f"  Set image for product: {product.name}")
