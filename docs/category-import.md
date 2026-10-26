# Approved Devika category import

The user approved the exact 29-label tree and use of the audit workbook as the import authority on 2026-10-26. The original Working workbook has not been independently verified. The original spellings and unresolved suffixes remain separate; approval covers the structure, not expanded meanings of abbreviations.

## Implemented locally

- `data/Devika_Clothings_Category_Audit.xlsx` is the supplied workbook, copied unchanged.
- `data/category_mapping.json` contains the approved 20 roots and 9 children plus their generated static banners.
- `store.0003_category_import_provenance` adds image paths, navigation visibility, stable source-label identities and immutable-by-import source-row provenance. Existing migration `0002_add_category_parent` is retained.
- Import stores 108 raw rows, including duplicates, blank descriptions and trailing spaces, with workbook SHA-256, worksheet and original row references.
- Importing again does not create categories or source rows again and does not overwrite staff edits to an imported category.
- Existing five demo categories remain active and retain their 15 product references. They are hidden from navigation only. The new source `SAREES` has a separate identity and collision-safe slug instead of adopting the legacy `Sarees` category.
- No products, prices, stock, payment records or order records are created or reassigned by the command. New categories correctly show zero products until verified products are assigned by staff.
- Uploaded category images take priority over generated static banners. Staff may edit category names, hierarchy, image, static banner path, ordering, visibility and active state. Product category choices show hierarchy and identify categories hidden from navigation.
- Parent filters and category counts include all active descendants, excluding inactive branches.

Local SQLite backup before migration/import: `/private/tmp/devika-before-category-import-yb0symj8.sqlite3`. Preserve it until the local import is accepted; this is not a production backup.

## Import commands

Run from the project root using the project Python environment:

```sh
python manage.py migrate store --plan
python manage.py migrate store
python manage.py import_categories --dry-run --hide-demo-navigation
python manage.py import_categories --hide-demo-navigation
python manage.py import_categories --dry-run --hide-demo-navigation
```

The final dry run should report 0 new categories and 0 new provenance rows. Dry-run runs the real transactional import then rolls it back. It requires the migration schema first. `--hide-demo-navigation` affects only the five named demo categories, not other staff-created categories; dependencies are printed and preserved. It does not archive or delete records.

Optional inputs:

```sh
python manage.py import_categories --source data/Devika_Clothings_Category_Audit.xlsx --mapping data/category_mapping.json --dry-run
```

The reader also supports `Working!B:C` in an original workbook, but do not substitute a different source without reconciling it against the approved mapping first. Unknown, missing or duplicate mapping labels abort the transaction. Slug conflicts are resolved for new identities with a literal-label hash, never by silently merging categories.

## Persistent Vercel database

1. Back up the persistent production database through its provider. Verify the controlled migration/import environment uses the exact `DATABASE_URL` used by the Vercel project. Do not print credentials, set an empty URL, or import into local/ephemeral SQLite expecting it to update production.
2. Ship/review the source workbook, mapping, command, model changes, both category migrations and templates together. Keep existing migrations. The core brand-default migration is included in the release; review the complete migration plan before deployment.
3. Review `python manage.py migrate store --plan`; apply the category migrations against that production database, then run the dry run. Confirm 29 exact labels, 108 rows, collision-safe identities and preserved existing dependencies before the real import.
4. Run the approved real import once; repeat dry-run to verify no additions. Independently verify product foreign keys, active product counts, all 29 links, uploaded-image URLs and staff edit forms.
5. Build CSS with `npm run build:css` and collect static files with `python manage.py collectstatic --noinput`. Deploy only after review and explicit deployment authorization. Do not run imports at application startup or on serverless requests.

The generated PNG source set is about 64 MiB. The obsolete hardcoded 15 MB function-size setting was removed before pushing. Static asset optimization and CDN hosting remain advisable; confirm the actual Vercel build completes within its runtime limits. Database migration/import must run separately against production.

## Validation

Seven focused tests cover transactional dry-run, repeat-import idempotency, 108-row fidelity, separate case variants, legacy product preservation, staff edits, recursive links/counts and cycle rejection. The stale order-prefix assertion was updated to the existing DVK prefix before pushing; no payment/order behavior was changed. The combined suite has 37 tests.
