from io import StringIO
from decimal import Decimal
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from core.forms import CategoryForm
from store.category_catalog import category_tree
from store.models import Category, CategoryImportLabel, CategorySourceRow, Product


class CategoryImportTest(TestCase):
    def run_import(self, **kwargs):
        call_command('import_categories', stdout=StringIO(), **kwargs)

    def test_dry_run_preserves_existing_data(self):
        old = Category.objects.create(name='Sarees', slug='sarees')
        self.run_import(dry_run=True, hide_demo_navigation=True)
        old.refresh_from_db()
        self.assertTrue(old.show_in_navigation)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(CategorySourceRow.objects.count(), 0)
        self.assertEqual(CategoryImportLabel.objects.count(), 0)

    def test_repeat_import_and_literal_source_preservation(self):
        self.run_import()
        self.run_import()
        self.assertEqual(Category.objects.count(), 29)
        self.assertEqual(CategoryImportLabel.objects.count(), 29)
        self.assertEqual(CategorySourceRow.objects.count(), 108)
        self.assertEqual(CategorySourceRow.objects.get(original_excel_row=71).original_description, '2PCs ')
        self.assertEqual(CategorySourceRow.objects.filter(original_description='').count(), 24)
        self.assertNotEqual(CategoryImportLabel.objects.get(source_label='lining material').category_id,
                            CategoryImportLabel.objects.get(source_label='Lining Material').category_id)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Category.objects.filter(parent__isnull=False).count(), 9)
        for identity in CategoryImportLabel.objects.select_related('category'):
            self.assertTrue(identity.category.static_image)
            self.assertEqual(self.client.get(reverse('store:category_detail', args=[identity.category.slug])).status_code, 200)

    def test_legacy_references_preserved_without_slug_adoption(self):
        legacy = Category.objects.create(name='Sarees', slug='sarees')
        product = Product.objects.create(name='Existing', slug='existing', category=legacy, base_price=Decimal('500'))
        self.run_import(hide_demo_navigation=True)
        legacy.refresh_from_db(); product.refresh_from_db()
        self.assertTrue(legacy.is_active)
        self.assertFalse(legacy.show_in_navigation)
        self.assertEqual(product.category_id, legacy.pk)
        self.assertNotEqual(CategoryImportLabel.objects.get(source_label='SAREES').category_id, legacy.pk)
        self.assertEqual(self.client.get('/category/sarees/').status_code, 200)

    def test_staff_edits_survive_reimport(self):
        self.run_import()
        category = CategoryImportLabel.objects.get(source_label='SAREE WEAVING').category
        category.name = 'Staff display label'; category.parent = None
        category.static_image = ''; category.show_in_navigation = False
        category.save()
        self.run_import()
        category.refresh_from_db()
        self.assertEqual(category.name, 'Staff display label')
        self.assertIsNone(category.parent)
        self.assertFalse(category.show_in_navigation)
        self.assertEqual(category.static_image, '')


class CategoryHierarchyTest(TestCase):
    def setUp(self):
        self.root = Category.objects.create(name='SAREES', slug='sarees')
        self.child = Category.objects.create(name='Linen', slug='linen', parent=self.root)
        self.grandchild = Category.objects.create(name='Checks', slug='checks', parent=self.child)
        self.inactive = Category.objects.create(name='Hidden branch', slug='hidden-branch', parent=self.root, is_active=False)
        self.inactive_child = Category.objects.create(name='Hidden child', slug='hidden-child', parent=self.inactive)
        for i, category in enumerate([self.root, self.child, self.grandchild, self.inactive_child]):
            Product.objects.create(name=f'Product {i}', slug=f'product-{i}', category=category, base_price=Decimal('500'))
        Product.objects.create(name='Inactive product', slug='inactive-product', category=self.child, base_price=Decimal('500'), is_active=False)

    def test_filters_and_counts_include_all_active_descendants(self):
        for url in [reverse('store:category_detail', args=[self.root.slug]), '/products/?category=sarees']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page_obj'].paginator.count, 3)
        tree = category_tree()
        self.assertEqual(tree[0].product_count, 3)
        self.assertEqual(tree[0].nav_children[0].nav_children[0].name, 'Checks')

    def test_dashboard_rejects_descendant_as_parent(self):
        form = CategoryForm(data={'name': 'SAREES', 'slug': 'sarees', 'parent': self.grandchild.pk, 'order': 0, 'is_active': True}, instance=self.root)
        self.assertFalse(form.is_valid())
        self.assertIn('parent', form.errors)

    def test_unrelated_products_not_in_category_filter(self):
        other = Category.objects.create(name='FROCK', slug='frock')
        Product.objects.create(name='Other', slug='other', category=other, base_price=Decimal('500'))
        response = self.client.get('/products/?category=sarees')
        self.assertEqual(response.context['page_obj'].paginator.count, 3)
