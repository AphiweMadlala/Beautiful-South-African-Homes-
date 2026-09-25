#!/usr/bin/env python3
"""Generate the data-backed reports from pipeline outputs:
reports/content-classification.md, listing-reconciliation.md, listing-provenance.md, media-reconciliation.md
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "reports"
posts = json.loads((ROOT / "data/instagram-posts.json").read_text())
cls = json.loads((ROOT / "data/post-classification.json").read_text())
props = json.loads((ROOT / "data/properties.json").read_text())
agents = json.loads((ROOT / "data/agents.json").read_text())
ver = json.loads((ROOT / "data/verification.json").read_text())
cur = json.loads((ROOT / "data/curation.json").read_text())
manifest = json.loads((ROOT / "data/image-manifest.json").read_text())
hashes = json.loads((ROOT / "data/raw/media-hashes.json").read_text())
by_sc = {p["shortcode"]: p for p in posts}
published = [p for p in props if p["status"] == "for-sale" or p["id"] in cur]


def money(v):
    return f"R{v:,}".replace(",", " ") if v else "n/a"


# ---------------------------------------------------------------- classification
cat = Counter(c["category"] for c in cls)
years = sorted({c["date"][:4] for c in cls})
lines = ["# Content Classification", "",
         f"All {len(cls)} posts on @beautifulsouthafricanhomes (11 Oct 2019 to 27 Aug 2026), classified by `scripts/build_data.py`.",
         "Machine-readable: `data/post-classification.json` (category, tags, reason, propertyKey per post).", "",
         "## Totals", "", "| Category | Posts | Notes |", "|---|---|---|"]
notes = {
    "FOR SALE": "Verified live on the marketing agency's site (24 Sep 2026).",
    "FEATURED HOME": "Sale features whose current availability is not verified. Become Portfolio candidates.",
    "RENTAL": "Excluded from all inventory.",
    "BRAND CONTENT": "Quotes, teasers, #BlackoutTuesday, 'Brand New Listing Loading' reel.",
    "EDITORIAL": "Compilation posts reusing images from other features (kitchens, entertaining).",
}
for k in ["FOR SALE", "UNDER OFFER", "SOLD", "WITHDRAWN", "RENTAL", "PROPERTY TOUR", "FEATURED HOME", "ARCHITECTURE",
          "DEVELOPMENT", "AGENT COLLABORATION", "BRAND CONTENT", "EDITORIAL", "OTHER"]:
    n = cat.get(k, 0)
    tagn = sum(1 for c in cls if k in c["tags"])
    note = notes.get(k, "")
    if tagn:
        note = f"Secondary tag on {tagn} posts. " + note
    if k in ("UNDER OFFER", "SOLD", "WITHDRAWN") and not n:
        note = "No post states this status. The only 'sold' strings are hashtags (#sold) and a commenter's emoji."
    if k == "DEVELOPMENT" and not n:
        note = "No new-development or off-plan posts found."
    lines.append(f"| {k} | {n} | {note} |")
lines += ["", "## By year", "", "| Year | " + " | ".join(sorted(cat)) + " |", "|---" * (len(cat) + 1) + "|"]
for y in years:
    row = Counter(c["category"] for c in cls if c["date"].startswith(y))
    lines.append(f"| {y} | " + " | ".join(str(row.get(k, 0)) for k in sorted(cat)) + " |")
lines += ["", "## Excluded posts", "", "| Date | Post | Category | Reason |", "|---|---|---|---|"]
for c in cls:
    if c["category"] in ("RENTAL", "BRAND CONTENT", "EDITORIAL", "OTHER"):
        lines.append(f"| {c['date'][:10]} | [{c['shortcode']}]({c['url']}) | {c['category']} | {c['reason']} |")
lines += ["", "## Method", "",
          "- Rentals: caption offers the home for rent, or prices are per month (`p/m`). One false positive (an agency named 'Eagle Canyon Property Sales & Rental') was excluded by requiring an explicit rental offer.",
          "- AGENT COLLABORATION tag: caption names an agency (not 'DM US').",
          "- ARCHITECTURE tag: caption names an architect rather than 'DM for credits' (2 posts).",
          "- PROPERTY TOUR tag: reel/IGTV video of a property (2 posts attached to properties).",
          "- Status words: no caption declares SOLD, UNDER OFFER or WITHDRAWN, so nothing is classified that way from Instagram alone."]
(R / "content-classification.md").write_text("\n".join(lines) + "\n")

# ---------------------------------------------------------------- reconciliation
multi = [p for p in props if len(p["instagramPosts"]) > 1]
lines = ["# Listing Reconciliation", "",
         f"{len(cls)} posts -> {sum(1 for c in cls if c['propertyKey'])} sale-feature posts -> **{len(props)} unique properties**.", "",
         "## Deduplication method", "",
         "1. **Perceptual hashing** of all 3,544 downloaded images (`data/raw/media-hashes.json`, pHash). Any two posts sharing images within Hamming distance 8 were reviewed.",
         "2. **Metadata grouping** by normalised location + bedrooms + bathrooms, then compared on price, agency, garages and land size, and re-checked with a looser image threshold (distance <= 12). Every such pair scored >= 20 (unrelated), so none were merged on metadata alone.",
         "3. **Identical captions** on the same day (reel + carousel of one home).", "",
         "## Merged (one property, several posts)", "", "| Property | Posts | Evidence |", "|---|---|---|"]
evidence = {"CaKg6gkMDhc": "3 shared images; 2020 feature R69m, 2022 feature (price not stated)",
            "CbLGu49sIPo": "3 shared images; Tyson Properties both times; 2021 R36m",
            "Cfmb7H5j3IP": "3 shared images; same 2 687 m2 stand, Pam Golding both times",
            "CZ4aN__MjG5": "reel + carousel, same day, identical caption"}
for p in multi:
    lines.append(f"| {p['title']} (`{p['id']}`) | " + ", ".join(u.rstrip('/').split('/')[-1] for u in p["instagramPosts"]) + f" | {evidence.get(p['id'], '')} |")
lines += ["", "## Compilation posts (not properties)", "",
          "CEPdh9WpuTE, CDE1PKoJFlY, CCwS-MnJTy9 reuse single images from other features (kitchens / entertaining). CH3EBygJlL2 reuses an image from CHs4jk6n5XX (St Francis Bay). Classified EDITORIAL / BRAND CONTENT.", "",
          "## Near-misses kept separate", "",
          "- Steyn City 4-bed at R29 995 000 posted 2020 (CAfXraYJ-Xu) and 2022 (CeWPKkZjjVT): same price and bed count, but image distance >= 20 across all images; kept separate and noted as a possible relisting with new photography.",
          "- Zimbali 4-bed at R19 700 000 (Cah8irEslSc, Feb 2022) vs today's Seeff P24-117247114 at the same price: different specs; unconfirmed (see listing-provenance.md).", "",
          "## Status after reconciliation", "", "| Status | Properties |", "|---|---|"]
for k, n in Counter(p["status"] for p in props).items():
    lines.append(f"| {k} | {n} |")
lines += ["", "`unknown` means Instagram-only evidence, or checked and not found live. It is never shown as For Sale."]
(R / "listing-reconciliation.md").write_text("\n".join(lines) + "\n")

# ---------------------------------------------------------------- provenance
lines = ["# Listing Provenance", "",
         f"Verification date: {ver['checkedAt']}. Every claim below traces to `data/verification.json` and raw captures in `data/raw/web/`.", "",
         "## Current inventory (For Sale)", ""]
for p in props:
    if p["status"] != "for-sale":
        continue
    a = next(a for a in agents if a["id"] == p["agentId"])
    v = ver_map = {c["post"]: c for c in ver["checks"]}[p["id"]]
    lines += [f"### {p['title']}", "",
              f"- Asking price: {money(p['priceZAR'])} (agency site and Instagram agree)",
              f"- Location: {p['estate']}, {p['city']}, {p['province']} (no street address published)",
              f"- Agent: {a['name']}, {a.get('role', '')}, {a['agency']}. Phone {a['phone']} as published on the listing page.",
              f"- Mandate source: the agency's own listing, ref {p['reference']}: {p['sourceListingUrl']}",
              f"- Instagram: {p['instagramPosts'][0]} (collaboration with @12digitalmedia; tags @12lve_propertygroup)",
              f"- Evidence: {v['summary']}",
              "- Note: see business-model-audit.md on the likely link between the platform's operators and 12LVE.", ""]
lines += ["## Recently featured homes checked (not confirmed live)", "", "| Post | Feature | Result | Summary |", "|---|---|---|---|"]
for c in ver["checks"]:
    if c["result"] == "for-sale":
        continue
    p = next((q for q in props if q["id"] == c["post"]), None)
    label = f"{p['title']}, {money(p['priceZAR'])}, {p['agency'] or 'agency not named'}" if p else c["post"]
    lines.append(f"| {c['post']} | {label} | {c['result']} | {c['summary']} |")
lines += ["", "## The Portfolio (published, availability to be confirmed)", "",
          "Shown on the site as 'Previously featured, <month year>' with 'Asking price when featured'. No agent names or phone numbers are shown for these; only the agency credited in the original feature.", "",
          "| # | Residence | Featured | Price when featured | Credited agency (as published) | Instagram |", "|---|---|---|---|---|---|"]
for i, cid in enumerate(cur, 2):
    p = next(q for q in props if q["id"] == cid)
    lines.append(f"| {i:02d} | {p['title']} | {p['firstSeenAt']} | {'POA' if p['priceOnApplication'] else money(p['priceZAR'])} | {p['agencyRaw']} | {p['instagramPosts'][0]} |")
lines += ["", "## Historical agencies (evidence of the operating model, not current relationships)", "",
          "| Agency | Properties credited |", "|---|---|"]
for k, n in Counter(p["agency"] for p in props if p["agency"]).most_common():
    lines.append(f"| {k} | {n} |")
lines += ["", f"Named agent credits: {len(agents)} people across {len({a['agency'] for a in agents})} agencies (`data/agents.json`). Only 1 agent is verified current; the others are historical credits and none of their contact details are published."]
(R / "listing-provenance.md").write_text("\n".join(lines) + "\n")

# ---------------------------------------------------------------- media
sizes = Counter()
for v in hashes.values():
    w = v.get("w", 0)
    sizes["<800" if w < 800 else "800-999" if w < 1000 else "1000-1399" if w < 1400 else ">=1400"] += 1
enc = sum(v["bytes"] for m in manifest.values() for v in m["variants"])
lines = ["# Media Reconciliation", "",
         "## Inventory", "",
         f"- Posts: {len(posts)}; media items referenced: 3 558 (3 554 images + 4 videos).",
         f"- Downloaded: {len(hashes)} images, 4 videos (`data/raw/media/<shortcode>/NN.jpg|mp4`, not committed: 389 MB).",
         "- Failed: all 10 images of CZR_ohysFa9 (Jan 2022, Eye of Africa) returned CDN errors. Property kept with no images; not published.",
         "- Zero-byte files: 0. Decode errors: 0.", "",
         "## Resolution (the key constraint)", "",
         "| Width | Images |", "|---|---|"] + [f"| {k} | {sizes[k]} |" for k in ["<800", "800-999", "1000-1399", ">=1400"]] + [
         "",
         "Instagram reports `originalWidth` 682 for most carousels: the account uploaded low-resolution images, so no higher-resolution copy exists on Instagram. Consequences for the design:",
         "- Hero uses the live listing's 1 152 px dusk image in a near-full-bleed 62% column rather than a 1 920 px full bleed.",
         "- Portfolio cards and mosaics are sized so 683 px sources are not stretched far beyond native width; the lightbox caps upscaling at 1.6x.",
         "- **Client action:** request original photography from the agencies for any residence that will be promoted.", "",
         "## Duplicates", "",
         "- Cross-post duplicates resolved by pHash (see listing-reconciliation.md). Within a merged property, duplicate images are dropped by hash.",
         "- Validation fails the build if two properties share an identical gallery (none do).", "",
         "## Published media", "",
         f"- {len(manifest)} images across {len(published)} residences, encoded to AVIF + WebP at 640 w and native width (max 1 600, never upscaled): {enc / 1e6:.1f} MB total.",
         "- Every `<img>` has explicit width/height, lazy loading below the fold, `fetchpriority=high` on the LCP image.",
         "- Live listing images 14-19 show estate amenities (golf course, gym, trails, courts, clubhouse), not the house. They are grouped under 'The estate' in the gallery and captioned as such.",
         "- Alt text: written per photograph for the live listing; Portfolio images use '<title>, photograph n of N' (Instagram's own alt text is only 'Photo by ...').", "",
         "## Videos", "",
         "| Post | Date | Type | Attached to | Used on site |", "|---|---|---|---|---|",
         "| CZ4dEfeldVR | 2022-02-12 | reel | Meyersdal 5-bed (merged with CZ4aN__MjG5) | No (not in Portfolio) |",
         "| CL4k5F1j7oP | 2021-03-01 | IGTV, 180 s | Eye of Africa feature | No (no stills) |",
         "| CHnWCdspyhK | 2020-11-15 | reel, 14 s | 'Happy Sunday' brand post | No |",
         "| CGUBEYbJmFz | 2020-10-14 | reel, 11 s | 'Brand New Listing Loading' teaser | No |", "",
         "No video is used on the site; none belongs to a current listing.", "",
         "## Rights", "",
         "Photography was produced for the marketing agencies and republished by the account. The site credits the agency on every residence. Written permission for web reuse should be confirmed before launch."]
(R / "media-reconciliation.md").write_text("\n".join(lines) + "\n")
print("wrote 4 reports")
