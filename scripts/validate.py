#!/usr/bin/env python3
"""Data + build validation. Exits non-zero on any error; prints warnings for legitimately missing optional data.

Errors: duplicate IDs/slugs, invalid prices, bad contacts, missing sources, broken/zero-byte media,
agent-reference errors, duplicate galleries, for-sale without provenance, broken internal links/images in docs/.
"""
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
errors, warnings = [], []
err = errors.append
warn = warnings.append

props = json.loads((ROOT / "data/properties.json").read_text())
agents = {a["id"]: a for a in json.loads((ROOT / "data/agents.json").read_text())}
verification = {c["post"]: c for c in json.loads((ROOT / "data/verification.json").read_text())["checks"]}
curation = json.loads((ROOT / "data/curation.json").read_text())
posts = json.loads((ROOT / "data/instagram-posts.json").read_text())
classes = {c["shortcode"]: c for c in json.loads((ROOT / "data/post-classification.json").read_text())}

# --- identity
for field in ("id", "slug"):
    for k, n in Counter(p[field] for p in props).items():
        if n > 1:
            err(f"duplicate {field}: {k}")
by_id = {p["id"]: p for p in props}
for cid in curation:
    if cid not in by_id:
        err(f"curation references unknown property {cid}")

# --- rentals / non-sales never become inventory
for p in props:
    for url in p["instagramPosts"]:
        sc = url.rstrip("/").split("/")[-1]
        if classes.get(sc, {}).get("category") in ("RENTAL", "BRAND CONTENT", "EDITORIAL"):
            err(f"{p['id']}: built from a {classes[sc]['category']} post {sc}")

# --- prices
for p in props:
    v = p["priceZAR"]
    if v is not None and (not isinstance(v, int) or v < 500_000 or v > 1_000_000_000):
        err(f"{p['id']}: implausible sale price {v}")
    if v is not None and p["priceOnApplication"]:
        err(f"{p['id']}: both a price and POA")
    if v is None and not p["priceOnApplication"]:
        warn(f"{p['id']}: no asking price in source")

# --- provenance
for p in props:
    if not p["sourceUrls"] or not p["instagramPosts"]:
        err(f"{p['id']}: missing sources")
    if p["status"] != "unknown":
        v = verification.get(p["id"])
        if not v or v["result"] != p["status"]:
            err(f"{p['id']}: status '{p['status']}' has no matching verification entry")
        if p["status"] == "for-sale" and not p["sourceListingUrl"]:
            err(f"{p['id']}: for-sale without a live listing URL")

# --- agents
for p in props:
    if p["agentId"] and p["agentId"] not in agents:
        err(f"{p['id']}: agentId {p['agentId']} not in agents.json")
for a in agents.values():
    if a["phone"] and not re.fullmatch(r"0\d{2} \d{3} \d{4}", a["phone"]):
        err(f"agent {a['id']}: malformed phone {a['phone']}")
    if a["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", a["email"]):
        err(f"agent {a['id']}: malformed email {a['email']}")
    if (a["phone"] or a["email"]) and not a["verified"]:
        err(f"agent {a['id']}: contact published without verification")
    for pid in a["credits"]:
        if pid not in by_id:
            err(f"agent {a['id']}: credit to unknown property {pid}")

# --- media
published = [p for p in props if p["status"] == "for-sale" or p["id"] in curation]
gallery_keys = Counter()
for p in props:
    if not p["images"]:
        warn(f"{p['id']}: no images")
    for img in p["images"]:
        f = ROOT / img["src"]
        if not f.exists():
            err(f"{p['id']}: missing media {img['src']}")
        elif f.stat().st_size == 0:
            err(f"{p['id']}: zero-byte media {img['src']}")
    gallery_keys[tuple(sorted(i["phash"] for i in p["images"]))] += 1
for k, n in gallery_keys.items():
    if k and n > 1:
        err(f"duplicate property gallery shared by {n} properties")
for p in published:
    if len(p["images"]) < 3:
        err(f"published {p['id']} has fewer than 3 images")
    if not p["agency"]:
        err(f"published {p['id']} has no credited agency")
    for field in ("erfSizeM2", "floorSizeM2", "garages"):
        if p[field] is None:
            warn(f"published {p['id']}: {field} unknown")

# --- built site: internal links and images resolve, no em/en dashes in visible copy
DOCS = ROOT / "docs"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.text = [], []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip += 1
        for key in ("href", "src", "data-src"):
            if a.get(key):
                self.refs.append(a[key])
        for key in ("srcset", "imagesrcset"):
            if a.get(key):
                self.refs += [part.strip().split(" ")[0] for part in a[key].split(",")]
        if a.get("alt"):
            self.text.append(a["alt"])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)


if DOCS.exists():
    for html in DOCS.rglob("*.html"):
        if html.name == "404.html":
            continue  # absolute base path, checked in browser QA
        parser = Links()
        parser.feed(html.read_text())
        visible = " ".join(parser.text)
        if re.search("[—–]", visible):
            err(f"{html.relative_to(ROOT)}: em/en dash in visible copy")
        for ref in parser.refs:
            u = urlparse(ref)
            if u.scheme or ref.startswith(("#", "mailto:", "tel:")) or ref.startswith("?"):
                continue
            target = (html.parent / unquote(u.path)).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                err(f"{html.relative_to(ROOT)}: broken link {ref}")
            elif target.stat().st_size == 0:
                err(f"{html.relative_to(ROOT)}: zero-byte asset {ref}")
    robots = (DOCS / "robots.txt").read_text()
    if "Disallow: /" not in robots:
        err("robots.txt does not disallow crawling in proposal mode")
    for html in DOCS.rglob("*.html"):
        if 'content="noindex, nofollow"' not in html.read_text():
            err(f"{html.relative_to(ROOT)}: missing noindex")
        if re.search(r"\b(proposal|demo|developer preview)\b", re.sub(r"<[^>]+>", " ", html.read_text()), re.I):
            err(f"{html.relative_to(ROOT)}: proposal wording visible to the client")
else:
    err("docs/ not built")

for w in warnings[:12]:
    print("WARN ", w)
if len(warnings) > 12:
    print(f"WARN  ... {len(warnings) - 12} more warnings")
for e in errors:
    print("ERROR", e)
print(f"\n{len(errors)} errors, {len(warnings)} warnings, {len(props)} properties, {len(published)} published")
sys.exit(1 if errors else 0)
