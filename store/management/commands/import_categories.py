import hashlib
import json
from collections import Counter
from pathlib import Path
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from store.category_workbook import read_source
from store.models import Category, CategoryImportLabel, CategorySourceRow


class Command(BaseCommand):
    help = 'Import approved literal category labels and source provenance; never creates or reassigns products.'

    def add_arguments(self, parser):
        parser.add_argument('--source', default=str(settings.BASE_DIR / 'data/Devika_Clothings_Category_Audit.xlsx'))
        parser.add_argument('--mapping', default=str(settings.BASE_DIR / 'data/category_mapping.json'))
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--hide-demo-navigation', action='store_true', help='Hide only the five legacy demo categories from navigation, keeping products and direct links.')

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            source = Path(options['source'])
            rows = read_source(source)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            mapping = json.loads(Path(options['mapping']).read_text())['categories']
            labels = [m['source_label'] for m in mapping]
            counts = Counter(r['original_label'] for r in rows)
            if len(labels) != len(set(labels)) or set(labels) != set(counts):
                raise ValueError('Source labels and approved mapping must match exactly; no silent omissions or aliases.')
            if any(m['parent'] and m['parent'] not in labels for m in mapping):
                raise ValueError('Unknown parent in mapping.')
            for m in mapping:
                chain, node = set(), m
                while node['parent']:
                    if node['source_label'] in chain:
                        raise ValueError('Mapping contains a category cycle.')
                    chain.add(node['source_label'])
                    node = next(x for x in mapping if x['source_label'] == node['parent'])
                if m['static_image'] and not (settings.BASE_DIR / 'static' / m['static_image']).is_file():
                    raise ValueError(f"Missing image for {m['source_label']}")
        except (OSError, ValueError, KeyError, BadZipFile, ParseError) as exc:
            raise CommandError(str(exc)) from exc

        categories, created_ids = {}, set()
        for position, entry in enumerate(mapping):
            identity = CategoryImportLabel.objects.filter(source_label=entry['source_label']).select_related('category').first()
            if identity:
                category = identity.category  # Preserve subsequent staff edits.
            else:
                base = slugify(entry['name']) or 'category'
                slug = base
                if Category.objects.filter(slug=slug).exists():
                    slug = base + '-' + hashlib.sha256(entry['source_label'].encode()).hexdigest()[:8]
                if Category.objects.filter(slug=slug).exists():
                    raise CommandError(f'Slug conflict for {entry["source_label"]}; resolve explicitly.')
                category = Category.objects.create(name=entry['name'], slug=slug, order=position,
                                                    static_image=entry['static_image'])
                CategoryImportLabel.objects.create(source_label=entry['source_label'], category=category)
                created_ids.add(category.pk)
            categories[entry['source_label']] = category
        for entry in mapping:
            category = categories[entry['source_label']]
            if category.pk in created_ids and entry['parent']:
                category.parent = categories[entry['parent']]
                category.full_clean()
                category.save(update_fields=['parent'])
        added_rows = 0
        for row in rows:
            identity = CategoryImportLabel.objects.get(source_label=row['original_label'])
            _, created = CategorySourceRow.objects.get_or_create(
                workbook_sha256=digest, sheet_name=row['sheet_name'], sheet_row=row['sheet_row'],
                defaults={**row, 'workbook_name': source.name, 'label': identity},
            )
            added_rows += created
        hidden = 0
        if options['hide_demo_navigation']:
            legacy = [('Sarees', 'sarees'), ('Salwar Sets & Suits', 'salwar-sets-suits'),
                      ('Kurtis & Tops', 'kurtis-tops'), ('Lehengas & Festive Wear', 'lehengas-festive-wear'),
                      ('Accessories & More', 'accessories-more')]
            for name, slug in legacy:
                for category in Category.objects.filter(name=name, slug=slug, show_in_navigation=True).exclude(pk__in=[c.pk for c in categories.values()]):
                    self.stdout.write(f'Hide legacy navigation: {name}; preserve {category.products.count()} products and {category.offer_set.count()} offer references.')
                    category.show_in_navigation = False
                    category.save(update_fields=['show_in_navigation'])
                    hidden += 1
        self.stdout.write(f'{len(mapping)} labels; {len(rows)} source rows; {len(created_ids)} new categories; {added_rows} new provenance rows; {hidden} legacy navigation entries hidden. No products changed.')
        if options['dry_run']:
            transaction.set_rollback(True)
            self.stdout.write('DRY RUN: all database changes rolled back.')
