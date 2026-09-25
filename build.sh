#!/usr/bin/env bash
# Full pipeline. Raw Instagram/web captures in data/raw are inputs; everything else is regenerated.
set -euo pipefail
cd "$(dirname "$0")"
python3 scripts/normalize_instagram.py   # data/raw -> data/instagram-posts.json
python3 scripts/build_data.py            # classification, dedup, properties, agents
python3 scripts/build_images.py          # AVIF/WebP for published residences (skips existing)
python3 scripts/build_site.py            # src + data -> docs/
python3 scripts/validate.py              # fails the build on data or link errors
