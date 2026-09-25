#!/usr/bin/env python3
"""Normalize the raw Apify Instagram export into data/instagram-posts.json.

Parses the account's templated captions (📍 location, Contact 📲, Agency🏛,
Architects, ▪️/▫️ feature bullets, 🇿🇦/🇺🇸/🇪🇺/🇬🇧 price lines) into fields.
Nothing is inferred beyond what the caption literally says.
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/instagram-posts-raw.json"
OUT = ROOT / "data/instagram-posts.json"


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip(" .:-|")


def field(caption, *labels):
    for label in labels:
        m = re.search(label + r"[^\n:]*:\s*([^\n]+)", caption, re.I)
        if m:
            v = clean(m.group(1))
            if v:
                return v
    return None


def money(s):
    """'R49 995 000.00' -> 49995000; returns None when not a number."""
    s = s.replace(" ", " ")
    m = re.search(r"(\d[\d ,]*(?:\.\d+)?)\s*(m|mil|million)?\b", s, re.I)
    if not m:
        return None
    num = m.group(1).replace(" ", "").replace(",", "")
    try:
        v = float(num)
    except ValueError:
        return None
    if m.group(2):
        v *= 1_000_000
    return int(round(v))


FLAG = {"🇿🇦": "ZAR", "🇺🇸": "USD", "🇪🇺": "EUR", "🇬🇧": "GBP"}


def prices(caption):
    out = {}
    text = caption.replace(" ", " ")
    for flag, cur in FLAG.items():
        # the flag must be followed by a currency amount or POA — flags also appear in prose
        for m in re.finditer(re.escape(flag) + r"\s*((?:R|\$|€|£)?\s?\d[^\n🇿🇺🇪🇬|]{0,38}|POA\b[^\n🇿🇺🇪🇬|]{0,20})", text):
            chunk = m.group(1).strip()
            entry = {"raw": chunk}
            if re.search(r"\bPOA\b|on application|on request", chunk, re.I):
                entry["poa"] = True
            else:
                entry["amount"] = money(chunk)
            if re.search(r"p/?m\b|per month|pm\b", chunk, re.I):
                entry["perMonth"] = True
            if re.search(r"p/?n\b|per night", chunk, re.I):
                entry["perNight"] = True
            out.setdefault(cur, entry)
    if "ZAR" not in out:
        # older posts: "price of 💰R17 250 000💰" or "asking price R…"
        m = re.search(r"\bR\s?(\d{1,3}(?:[ ,]\d{3})+|\d+(?:\.\d+)?\s?(?:m|million))\b", text)
        if m:
            out["ZAR"] = {"raw": m.group(0), "amount": money(m.group(1)), "inferredFromProse": True}
    return out


def bullets(caption):
    items = []
    for line in caption.splitlines():
        m = re.match(r"\s*[▪▫◾◽•][️]?\s*(.+)", line)
        if m:
            items.append(clean(m.group(1)))
    return items


def num_from(items, caption, pattern):
    for it in items:
        m = re.match(r"(\d+(?:[.,]\d+)?)\s*(?:x\s*)?" + pattern, it, re.I)
        if m:
            return float(m.group(1).replace(",", "."))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:spacious\s+)?" + pattern, caption, re.I)
    if m:
        return float(m.group(1).replace(",", "."))
    return None


def sizes(items, caption):
    land = floor = None
    text = "\n".join(items) + "\n" + caption
    m = re.search(r"(\d[\d ,]*)\s*(?:m2|m²|sqm|sq m|square metres?)\s*(?:land|stand|erf)", text, re.I) or \
        re.search(r"(?:land|stand|erf)[^\d\n]{0,25}(\d[\d ,]*)\s*(?:m2|m²|sqm)", text, re.I) or \
        re.search(r"(\d[\d ,]*)\s*(?:land)\s*(?:sqm|m2)", text, re.I)
    if m:
        land = int(m.group(1).replace(" ", "").replace(",", ""))
    m = re.search(r"(\d[\d ,]*)\s*(?:m2|m²|sqm)\s*(?:under roof|floor)", text, re.I) or \
        re.search(r"under roof(?: size)?(?: of)?\s*(\d[\d ,]*)\s*(?:m2|m²|sqm)", text, re.I)
    if m:
        floor = int(m.group(1).replace(" ", "").replace(",", ""))
    if re.search(r"(\d+(?:\.\d+)?)\s*hectare", text, re.I) and not land:
        land = int(float(re.search(r"(\d+(?:\.\d+)?)\s*hectare", text, re.I).group(1)) * 10000)
    return land, floor


def nfkc(s):
    return unicodedata.normalize("NFKC", s or "")


def main():
    raw = json.loads(RAW.read_text())
    posts = []
    for x in raw:
        cap = x.get("caption") or ""
        items = bullets(cap)
        land, floor = sizes(items, cap)
        media = []
        kids = x.get("childPosts") or []
        if kids:
            for i, c in enumerate(kids):
                media.append({
                    "index": i,
                    "type": "video" if c.get("type") == "Video" else "image",
                    "id": c.get("id"),
                    "url": c.get("displayUrl"),
                    "videoUrl": c.get("videoUrl"),
                    "width": c.get("dimensionsWidth"),
                    "height": c.get("dimensionsHeight"),
                    "alt": c.get("alt"),
                })
        else:
            media.append({
                "index": 0,
                "type": "video" if x.get("type") == "Video" else "image",
                "id": x.get("id"),
                "url": x.get("displayUrl"),
                "videoUrl": x.get("videoUrl"),
                "width": x.get("dimensionsWidth"),
                "height": x.get("dimensionsHeight"),
                "alt": x.get("alt"),
            })
        loc_line = None
        m = re.search(r"📍\s*([^\n]+)", cap)
        if m:
            loc_line = clean(m.group(1))
        posts.append({
            "id": x["id"],
            "shortcode": x["shortCode"],
            "url": x["url"],
            "date": x["timestamp"],
            "mediaType": {"Sidecar": "carousel", "Image": "image", "Video": "video"}.get(x["type"], x["type"]),
            "productType": x.get("productType"),
            "caption": cap,
            "coverImage": x.get("displayUrl"),
            "media": media,
            "video": {"url": x.get("videoUrl"), "durationS": x.get("videoDuration"), "views": x.get("videoViewCount")} if x.get("videoUrl") else None,
            "author": x.get("ownerUsername"),
            "collaborators": [c.get("username") for c in x.get("coauthorProducers") or []],
            "taggedUsers": [t.get("username") for t in x.get("taggedUsers") or []],
            "taggedLocation": {"name": x.get("locationName"), "id": x.get("locationId")} if x.get("locationName") else None,
            "hashtags": x.get("hashtags") or [],
            "mentions": x.get("mentions") or [],
            "alt": x.get("alt"),
            "likes": x.get("likesCount"),
            "comments": x.get("commentsCount"),
            "firstComment": x.get("firstComment"),
            "parsed": {
                "locationLine": loc_line,
                "contact": field(cap, r"Contact\s*📲", r"Contact"),
                "details": field(cap, r"Details"),
                "agency": field(cap, r"Agency\s*🏛", r"Agency"),
                "architects": field(cap, r"Architects?"),
                "photographer": (re.search(r"📸?📷?\s*:?\s*@([\w.]+)", cap).group(1)
                                 if re.search(r"(?:📸|📷)\s*:?\s*@([\w.]+)", cap) else None),
                "bullets": items,
                "bedrooms": num_from(items, cap, r"bed(?:room)?s?\b"),
                "bathrooms": num_from(items, cap, r"(?:and a half\s+)?bath(?:room)?s?\b"),
                "garages": num_from(items, cap, r"car garage"),
                "landM2": land,
                "floorM2": floor,
                "prices": prices(cap),
                "rental": bool(re.search(r"\brental\b|for rent\b|to rent\b|p/m\b|per month|per night|p/n\b|holiday let|short.?term", cap, re.I)),
                "soldMention": bool(re.search(r"\bSOLD\b|under offer", cap)),
            },
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    OUT.write_text(json.dumps(posts, ensure_ascii=False, indent=1))
    print(f"wrote {len(posts)} posts -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
