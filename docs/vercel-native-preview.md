# Native Django preview: bundle-size correction

Branch: `fix/vercel-native-django`. Production/main is not changed by this branch.

## Minimal changes

- Ignore `/staticfiles/` and remove generated assets from Git's index with `git rm --cached`; local collected files and all original `static/` and `media/` files remain on disk.
- Replace legacy `builds`/`routes` with `framework: django`. Native detection uses `manage.py` and the existing `WSGI_APPLICATION = config.wsgi.application`.
- Keep the existing Django `STATIC_URL`, `STATIC_ROOT`, WhiteNoise compressed manifest backend, middleware, default media storage and database/authentication/payment settings unchanged.
- The build command installs the lockfile's Tailwind tools and compiles `static/css/main.css`. Python dependency installation and `collectstatic` are performed by native Vercel Django integration, not repeated by the custom build script.
- The Python function excludes `static/**`, `staticfiles/**` and `docs/**`. These are not upload exclusions: source assets must reach the builder so collectstatic can publish them to the CDN. Templates, app code, migrations, category data, fixtures and media are retained.
- Vercel's native Django builder explicitly puts `staticfiles/staticfiles.json` back into the function after exclusions. This preserves manifest URL resolution without bundling the image files. Confirmed in `@vercel/python` 28.0.2's `runDjangoCollectStatic` and `packFunctionBundle` implementation.
- No function size limit is increased. No automatic migration, fixture loading or category import is added to the build or startup.

## Local verification

- Django checks and all 37 existing tests pass.
- An isolated copy collected assets to a separate CDN directory, then constructed a runtime tree with no `static/`, no `docs/` and only `staticfiles.json` under `staticfiles/`.
- That tree rendered the homepage, product list, one product detail, `/dashboard/login/`, cart, checkout with a test cart and all 29 category routes using an isolated temporary database. No payment request was made.
- CSS, animation JavaScript, transparent logo and every category PNG resolve through the generated manifest and exist in the CDN output.
- Function application files: 3,092,491 bytes, **excluding installed Python dependencies**. CDN output: 142,262,958 bytes. Retained manifest: 14,659 bytes. These are local artifact measurements, not a claimed deployed bundle size.
- SHA-256 checks confirmed all 64 original static/media files remain unchanged after the build.

## Preview acceptance

Push this branch only. The Git-connected Vercel project should create a Preview deployment. `framework` and `buildCommand` in vercel.json override the project's legacy framework/build command; remove any manually configured output-directory override if it prevents native detection.

Do not promote or merge until the preview confirms:

1. Build uses native Django and publishes collected assets to the CDN.
2. Actual function bundle is below the reported 225 MB project limit; obtain the byte size from deployment output/logs, not the local app-only figure.
3. Homepage, CSS, JavaScript, logo and category images return successful responses; static requests do not invoke Python.
4. Product pages, staff login and checkout work against an isolated Preview database. Use Razorpay test-mode credentials. Never submit a live charge merely to smoke-test routes.
5. No database migration/import was run against production as part of this preview. If Preview currently shares a production DATABASE_URL, do not mutate its data; provision an isolated database branch first.
6. Preserve existing environment variables. Production database schema/import still needs a separately reviewed release step if it has not been applied.

## Admin uploads: separate persistent-storage migration

All current `media/` files remain tracked and packaged. No model file paths, database values or media settings are changed by this bundle fix. Bundled media is read-only deployment content, not durable storage for new uploads. The existing project also needs production `/media/` delivery verified; native static CDN support does not make MEDIA_ROOT persistent.

Safe follow-up plan:

1. Inventory every nonempty ImageField in StoreSettings.logo, Banner.image, Category.image and ProductImage.image on the persistent database. Compare each exact relative key to available files and identify missing objects before changing URLs. The local database does not establish which production media is referenced.
2. Back up both database references and media bytes, with file sizes and SHA-256 hashes.
3. Provision a dedicated S3-compatible media bucket and credentials restricted to that bucket/prefix. Install `django-storages[s3]` in a separate reviewed change. Configure only the `default` storage alias; preserve the staticfiles backend so static assets continue using Vercel CDN.
4. Copy bytes to object keys matching current ImageField relative names exactly, including their products/, categories/, banners/ and brand/ prefixes. Do not overwrite different bytes silently. Verify checksums and test object URL access. Existing database keys need not be rewritten if keys are preserved.
5. Switch media storage in Preview with provider credentials and an isolated database, keeping production storage unchanged. Test image upload, display, deletion behavior, private/public URL policy and persistence after redeployment. Use collision-safe uploads (`file_overwrite=False`) and do not infer that an existing file is disposable because it has a duplicate-looking filename.
6. Only after review, switch production storage. Keep original media and backups through acceptance/rollback; remove bundled media only in a later explicit change after every referenced key is verified in object storage.

No bucket, credentials or provider-specific media configuration is fabricated here.

## Sources

- https://vercel.com/docs/frameworks/full-stack/django
- https://vercel.com/docs/project-configuration/vercel-json
- https://github.com/vercel/vercel/tree/main/packages/python
- https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
