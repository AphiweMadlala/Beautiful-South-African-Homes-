# Project Context: Beautiful South African Homes website (proposal)

## What this is

A proposal website for **@beautifulsouthafricanhomes**, an Instagram property media platform (28.6k followers, since 2019) that features South African residences marketed by external agencies. The site is a sibling in spirit to Exclusive Cape Town (dark editorial luxury) but built for **national residential sales**, not villa stays.

- Built output: `docs/` (GitHub Pages ready, relative links; `404.html` assumes the base path `/Beautiful-South-African-Homes-/`, set in `scripts/build_site.py` as `SITE_BASE`).
- Proposal mode: `PROPOSAL_MODE = True` in `scripts/build_site.py` adds `noindex, nofollow` to every page and a Disallow-all `robots.txt`. Nothing visible says "proposal" or "demo" (validator enforces this).

## Key facts that shape everything

1. **One verified residence for sale** (Eye of Africa, R9m, 12LVE Property Group, agent Gabriel Masilo), verified 24 Sep 2026. The other 25 published homes are **The Portfolio**: previously featured, availability to be confirmed, price labelled "Asked when featured" with the month.
2. **Not verified as an agency.** Evidence points to the account being linked to the principals of 12LVE / @real_estate_bros. See `reports/business-model-audit.md`. The site makes no mandate claims either way.
3. **Source photos are mostly 682 px wide.** The layout is designed around that; ask agencies for originals.
4. **Rentals are excluded** (2 rental posts).

## Pipeline

```
./build.sh
  scripts/normalize_instagram.py  data/raw/instagram-posts-raw.json -> data/instagram-posts.json
  scripts/build_data.py           -> data/post-classification.json, data/properties.json, data/agents.json
  scripts/build_images.py         published images -> src/assets/img (AVIF + WebP), data/image-manifest.json
  scripts/build_site.py           src/templates + src/assets + data -> docs/
  scripts/validate.py             fails on data/link/provenance errors
scripts/write_reports.py          regenerates the 4 data-backed reports
```

Inputs you edit by hand:
- `data/verification.json`: every non-`unknown` status must have an entry here (validator enforces).
- `data/curation.json`: ordered list of Portfolio property IDs to publish.
- `scripts/build_data.py`: gazetteer (location to province/city/area/estate), agency canonical names, feature taxonomy, merge groups.
- `scripts/build_site.py`: live-listing alt text and story, featured/signature selection, province images.

Raw captures (`data/raw/`) are committed except `data/raw/media/` (389 MB of Instagram originals; re-download with the Apify dataset or keep locally).

## Updating inventory

1. Scrape new posts (Apify `instagram-scraper`, `resultsLimit` N) into `data/raw/instagram-posts-raw.json`, download media.
2. Verify each new listing on the agency site; add an entry to `data/verification.json` (result `for-sale`, sources, raw capture path).
3. Add the verified agent contact in `scripts/build_data.py` only from the agency's own page.
4. `./build.sh`, then `node qa/qa.mjs` (see `reports/final-qa.md`).

## QA

`qa/qa.mjs` (Playwright) checks 13 page types at 7 widths plus the All Residences default and register filters, filters, URL state, Back/Forward, price and status on every card view, menu, filters sheet, the single gallery and lightbox, property section numbering, contact links, reduced motion, touch targets and a full internal link crawl. Serve `docs/` under `/Beautiful-South-African-Homes-/` on port 8321 first.

## Reports

`reports/`: business-model-audit, research-audit, brand-audit, content-classification, listing-reconciliation, listing-provenance, media-reconciliation, final-qa. Design system: `DESIGN.md`.

## Open client questions

- Confirm who operates the account and its relationship to 12LVE / @real_estate_bros.
- Are features paid? Is the "feature your listing" service still offered?
- Vector logo (the gold monogram) and permission to reuse agency photography.
- Original high-resolution photography for promoted residences.
- A domain; then set `SITE_BASE`, canonical URLs, and turn off `PROPOSAL_MODE` at launch.
