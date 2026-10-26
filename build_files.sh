#!/bin/sh
set -eu

# Native Django builds install Python dependencies before this command.
# Vercel runs collectstatic afterwards and publishes STATIC_ROOT to its CDN.
npm ci --include=dev
npm run build:css
