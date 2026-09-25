#!/usr/bin/env python3
"""Classify posts, deduplicate properties and emit canonical data.

Inputs:  data/instagram-posts.json, data/verification.json, data/raw/media-hashes.json
Outputs: data/post-classification.json, data/properties.json, data/agents.json

Rules:
- Rentals, brand/editorial and compilation posts never become sales inventory.
- A status other than "unknown" requires an entry in data/verification.json.
- Missing data stays null. Titles are descriptive labels built from verified fields only.
"""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = json.loads((ROOT / "data/instagram-posts.json").read_text())
VERIFY = json.loads((ROOT / "data/verification.json").read_text())
HASHES = json.loads((ROOT / "data/raw/media-hashes.json").read_text())
TODAY = VERIFY["checkedAt"]

# ---------------------------------------------------------------------------
# Gazetteer: first match wins. (pattern, province, city, area, estate)
GAZ = [
    (r"eye of africa", "Gauteng", "Johannesburg", "Eikenhof", "Eye of Africa Golf & Residential Estate"),
    (r"meyersdal eco", "Gauteng", "Johannesburg", "Meyersdal", "Meyersdal Eco Estate"),
    (r"meyersdal nature", "Gauteng", "Johannesburg", "Meyersdal", "Meyersdal Nature Estate"),
    (r"meyersdal", "Gauteng", "Johannesburg", "Meyersdal", None),
    (r"aspen (hills|nature)", "Gauteng", "Johannesburg", "Aspen Hills", "Aspen Hills Nature Estate"),
    (r"eagle canyon", "Gauteng", "Johannesburg", "Honeydew", "Eagle Canyon Golf Estate"),
    (r"steyn city", "Gauteng", "Johannesburg", "Fourways", "Steyn City"),
    (r"dainfern", "Gauteng", "Johannesburg", "Fourways", "Dainfern Golf & Country Estate"),
    (r"helderfontein", "Gauteng", "Johannesburg", "Fourways", "Helderfontein Estate"),
    (r"ebotse", "Gauteng", "Benoni", "Rynfield", "Ebotse Golf & Country Estate"),
    (r"waterfall equestrian", "Gauteng", "Midrand", "Waterfall", "Waterfall Equestrian Estate"),
    (r"waterfall country", "Gauteng", "Midrand", "Waterfall", "Waterfall Country Estate"),
    (r"kyalami", "Gauteng", "Midrand", "Kyalami", "Kyalami Estate"),
    (r"midstream", "Gauteng", "Centurion", "Midstream", "Midstream Estate"),
    (r"blue hills", "Gauteng", "Midrand", "Blue Hills", "Blue Hills Equestrian Estate"),
    (r"boardwalk meander", "Gauteng", "Pretoria", "Olympus", "Boardwalk Meander"),
    (r"blai?re? atholl", "Gauteng", "Centurion", "Blair Atholl", "Blair Atholl Golf Estate"),
    (r"copperleaf", "Gauteng", "Centurion", "Copperleaf", "Copperleaf Golf & Country Estate"),
    (r"centurion golf", "Gauteng", "Centurion", "Centurion", "Centurion Golf Estate"),
    (r"silver lakes", "Gauteng", "Pretoria", "Silver Lakes", "Silver Lakes Golf Estate"),
    (r"mooikloof", "Gauteng", "Pretoria", "Mooikloof", "Mooikloof Equestrian Estate"),
    (r"blue valley", "Gauteng", "Centurion", "Blue Valley", "Blue Valley Golf Estate"),
    (r"serengeti", "Gauteng", "Kempton Park", "Serengeti", "Serengeti Golf & Wildlife Estate"),
    (r"featherbrooke", "Gauteng", "Krugersdorp", "Featherbrooke", "Featherbrooke Estate"),
    (r"saddlebrook", "Gauteng", "Midrand", "Saddlebrook", "Saddlebrook Estate"),
    (r"dunblane", "Gauteng", "Midrand", "Dunblane", "Dunblane Equestrian Estate"),
    (r"alberante", "Gauteng", "Alberton", "Alberante", None),
    (r"bensch", "Gauteng", "Benoni", "Benoni North", None),
    (r"benoni", "Gauteng", "Benoni", "Benoni", None),
    (r"glenvista", "Gauteng", "Johannesburg", "Glenvista", None),
    (r"hartbeespoort|birdwood|westlake|the islands estate", "North West", "Hartbeespoort", "Hartbeespoort", None),
    (r"houghton", "Gauteng", "Johannesburg", "Houghton Estate", None),
    (r"hyde park", "Gauteng", "Johannesburg", "Hyde Park", None),
    (r"hurlingham", "Gauteng", "Johannesburg", "Hurlingham", None),
    (r"inanda", "Gauteng", "Johannesburg", "Inanda", None),
    (r"illovo", "Gauteng", "Johannesburg", "Illovo", None),
    (r"sandhurst", "Gauteng", "Johannesburg", "Sandhurst", None),
    (r"sandown|michelangelo|capital on the park|rafael", "Gauteng", "Johannesburg", "Sandown", None),
    (r"bryanston", "Gauteng", "Johannesburg", "Bryanston", None),
    (r"parkmore", "Gauteng", "Johannesburg", "Parkmore", None),
    (r"morningside", "Gauteng", "Johannesburg", "Morningside", None),
    (r"sunninghill", "Gauteng", "Johannesburg", "Sunninghill", None),
    (r"atholl", "Gauteng", "Johannesburg", "Atholl", None),
    (r"birdhaven", "Gauteng", "Johannesburg", "Birdhaven", None),
    (r"melrose", "Gauteng", "Johannesburg", "Melrose", None),
    (r"dunkeld", "Gauteng", "Johannesburg", "Dunkeld", None),
    (r"rosebank", "Gauteng", "Johannesburg", "Rosebank", None),
    (r"saxonwold", "Gauteng", "Johannesburg", "Saxonwold", None),
    (r"westcliff", "Gauteng", "Johannesburg", "Westcliff", None),
    (r"craighall", "Gauteng", "Johannesburg", "Craighall Park", None),
    (r"northcliff", "Gauteng", "Johannesburg", "Northcliff", None),
    (r"waverl", "Gauteng", "Johannesburg", "Waverley", None),
    (r"oriel|essexwold|bedford", "Gauteng", "Johannesburg", "Bedfordview", None),
    (r"zimbali", "KwaZulu-Natal", "Ballito", "Zimbali", "Zimbali Coastal Resort & Estate"),
    (r"simbithi", "KwaZulu-Natal", "Ballito", "Simbithi", "Simbithi Eco Estate"),
    (r"zululami", "KwaZulu-Natal", "Ballito", "Zululami", "Zululami Luxury Coastal Estate"),
    (r"ballito", "KwaZulu-Natal", "Ballito", "Ballito", None),
    (r"hawaan", "KwaZulu-Natal", "Umhlanga", "Umhlanga", "Hawaan Forest Estate"),
    (r"la lucia", "KwaZulu-Natal", "Umhlanga", "La Lucia", None),
    (r"umhlanga", "KwaZulu-Natal", "Umhlanga", "Umhlanga Rocks", None),
    (r"cotswold", "KwaZulu-Natal", "Hillcrest", "Hillcrest", "Cotswold Downs Estate"),
    (r"assagay", "KwaZulu-Natal", "Hillcrest", "Assagay", None),
    (r"camps bay", "Western Cape", "Cape Town", "Camps Bay", None),
    (r"bakoven", "Western Cape", "Cape Town", "Bakoven", None),
    (r"bantry bay", "Western Cape", "Cape Town", "Bantry Bay", None),
    (r"clifton", "Western Cape", "Cape Town", "Clifton", None),
    (r"fresnaye", "Western Cape", "Cape Town", "Fresnaye", None),
    (r"llandudno", "Western Cape", "Cape Town", "Llandudno", None),
    (r"sea point", "Western Cape", "Cape Town", "Sea Point", None),
    (r"hout bay|constanta close", "Western Cape", "Cape Town", "Hout Bay", None),
    (r"constantia", "Western Cape", "Cape Town", "Constantia", None),
    (r"waterfront", "Western Cape", "Cape Town", "V&A Waterfront", None),
    (r"bloubergstrand", "Western Cape", "Cape Town", "Bloubergstrand", None),
    (r"atlantic beach", "Western Cape", "Cape Town", "Melkbosstrand", "Atlantic Beach Golf Estate"),
    (r"platterkloof", "Western Cape", "Cape Town", "Platterkloof", "Baronetcy Estate"),
    (r"val de vi", "Western Cape", "Paarl", "Val de Vie", "Val de Vie Estate"),
    (r"brandwacht|die boord|stellenbosch", "Western Cape", "Stellenbosch", "Stellenbosch", None),
    (r"helderrand", "Western Cape", "Somerset West", "Helderrand", None),
    (r"franschhoek", "Western Cape", "Franschhoek", "Franschhoek", None),
    (r"pezula", "Western Cape", "Knysna", "Pezula", "Pezula Private Estate"),
    (r"simola", "Western Cape", "Knysna", "Simola", "Simola Golf & Country Estate"),
    (r"thesen", "Western Cape", "Knysna", "Thesen Islands", None),
    (r"the heads", "Western Cape", "Knysna", "The Heads", None),
    (r"knysna", "Western Cape", "Knysna", "Knysna", None),
    (r"plett", "Western Cape", "Plettenberg Bay", "Plettenberg Bay", None),
    (r"oubaai", "Western Cape", "George", "Herolds Bay", "Oubaai Golf Estate"),
    (r"pinnacle point|mossel bay", "Western Cape", "Mossel Bay", "Pinnacle Point", "Pinnacle Point Golf Estate"),
    (r"wilderness", "Western Cape", "Wilderness", "Wilderness", None),
    (r"st francis", "Eastern Cape", "St Francis Bay", "St Francis Bay", None),
    (r"summerstrand|summerstand", "Eastern Cape", "Gqeberha", "Summerstrand", None),
    (r"port alfred|royal alfred", "Eastern Cape", "Port Alfred", "Royal Alfred Marina", "Royal Alfred Marina"),
    (r"cape winelands", "Western Cape", "Cape Winelands", None, None),
    (r"cape town", "Western Cape", "Cape Town", None, None),
]


def locate(text):
    t = unicodedata.normalize("NFKC", text or "").lower()
    for pat, prov, city, area, estate in GAZ:
        if re.search(pat, t):
            return {"province": prov, "city": city, "area": area, "estate": estate}
    return None


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ---------------------------------------------------------------------------
AGENCY_CANON = [
    (r"pam gol[df]ing", "Pam Golding Properties"),
    (r"seeff", "Seeff Property Group"),
    (r"re/?max|remax", "RE/MAX"),
    (r"rawson", "Rawson Property Group"),
    (r"azure", "Azure Coastal Real Estate (eXp Realty)"),
    (r"hamilton", "Hamilton's Property Portfolio"),
    (r"sotheby", "Lew Geffen Sotheby's International Realty"),
    (r"cha[sz] everitt", "Chas Everitt International Property Group"),
    (r"jawitz", "Jawitz Properties"),
    (r"allegiance", "Allegiance Properties Soma"),
    (r"kent gush", "Kent Gush Properties"),
    (r"fine ?(&|and) ?country", "Fine & Country"),
    (r"engel", "Engel & Völkers"),
    (r"harcourts", "Harcourts"),
    (r"tyson", "Tyson Properties"),
    (r"vered", "Vered Estates"),
    (r"12lve", "12LVE Property Group"),
    (r"lance", "Lance Real Estate"),
    (r"dogon", "Dogon Group Properties"),
    (r"zareena", "Zareena Kara Properties"),
    (r"firzt", "Firzt Realty"),
    (r"platinum", "Platinum Residential"),
    (r"lionlead", "Lionlead Real Estate"),
    (r"quay ?1", "Quay 1 International Realty"),
    (r"century 21", "Century 21"),
    (r"kw eden|keller", "Keller Williams Eden"),
]


def agency_canon(raw):
    if not raw or re.search(r"\bDM\b", raw, re.I):
        return None
    for pat, name in AGENCY_CANON:
        if re.search(pat, raw, re.I):
            return name
    return raw.strip()


def contact_names(raw):
    """Return person names from the Contact line; handles and 'DM US' are not names."""
    if not raw or re.search(r"\bDM\b", raw, re.I):
        return []
    parts = re.split(r"\s*(?:&|,| and )\s*", raw)
    return [p.strip() for p in parts if p.strip() and not p.strip().startswith("@")]


FEATURES = [
    ("pool", r"pool"),
    ("ocean-views", r"ocean|sea view|atlantic|beach"),
    ("golf-estate", r"golf"),
    ("home-gym", r"\bgym\b"),
    ("cinema", r"cinema|theatre"),
    ("wine-cellar", r"wine cellar|cellar"),
    ("home-automation", r"automation|smart home|automated"),
    ("solar-backup", r"solar|inverter|backup"),
    ("flatlet", r"flatlet|cottage|guest suite"),
    ("elevator", r"elevator|\blift\b"),
    ("equestrian", r"equestrian|stable"),
    ("entertainment-area", r"entertain|braai|boma|bar\b|fire ?pit"),
    ("mountain-views", r"mountain|table mountain|valley view"),
    ("secure-estate", r"estate|24/7 security|security estate"),
]
FEATURE_LABEL = {
    "pool": "Swimming pool", "ocean-views": "Ocean views", "golf-estate": "Golf estate",
    "home-gym": "Private gym", "cinema": "Cinema room", "wine-cellar": "Wine cellar",
    "home-automation": "Home automation", "solar-backup": "Solar & backup power",
    "flatlet": "Guest flatlet", "elevator": "Residential lift", "equestrian": "Equestrian",
    "entertainment-area": "Entertainment areas", "mountain-views": "Mountain views",
    "secure-estate": "Secure estate", "large-garaging": "Garaging for 4+", "large-stand": "Stand over 2,000 m²",
}


def features_for(q, caption, loc):
    blob = " ".join(q["bullets"]).lower()
    out = []
    for key, pat in FEATURES:
        if key == "secure-estate":
            if loc and loc.get("estate"):
                out.append(key)
            continue
        if key == "golf-estate":
            if re.search(pat, blob) or (loc and loc.get("estate") and "golf" in loc["estate"].lower()):
                out.append(key)
            continue
        if re.search(pat, blob):
            out.append(key)
    if (q["garages"] or 0) >= 4:
        out.append("large-garaging")
    if (q["landM2"] or 0) >= 2000:
        out.append("large-stand")
    return out


# ---------------------------------------------------------------------------
BRAND = {"CKYvTW9j4W4", "CH3EBygJlL2", "CHnWCdspyhK", "CGUBEYbJmFz", "CA72WJCphyu", "CAlMK7lJIj4",
         "B_ked9XFUQ0", "B_j3U0klNiN", "B_i2YkFlMWr"}
COMPILATION = {"CEPdh9WpuTE", "CDE1PKoJFlY", "CCwS-MnJTy9"}
# same property across posts, established by perceptual-hash image matches or identical captions
MERGE = [
    ["CaKg6gkMDhc", "CFPzw5HpYLy"],       # Waterfall Equestrian - 3 shared images
    ["CbLGu49sIPo", "COybHiZDNrI"],       # Hout Bay - 3 shared images
    ["Cfmb7H5j3IP", "CXDuVM6M1lu"],       # Zimbali 6-bed, 2 687 m2 - 3 shared images
    ["CZ4aN__MjG5", "CZ4dEfeldVR"],       # Meyersdal carousel + reel, same day, identical caption
]
VERIFIED = {c["post"]: c for c in VERIFY["checks"]}


def classify(x):
    q = x["parsed"]
    cap = x["caption"]
    sc = x["shortcode"]
    tags = []
    if sc in BRAND:
        return "BRAND CONTENT", tags, "no listing data; motivational / teaser / cause post"
    if sc in COMPILATION:
        return "EDITORIAL", tags, "multi-property compilation reusing images from other features"
    z = q["prices"].get("ZAR", {})
    if q["rental"] and (z.get("perMonth") or re.search(r"for rental|up for rental|rental acquisition", cap, re.I)):
        return "RENTAL", tags, "caption offers the home for rent" + (" (price per month)" if z.get("perMonth") else "")
    if x["mediaType"] == "video":
        tags.append("PROPERTY TOUR")
    if re.search(r"architect", cap, re.I) and q["architects"] and not re.search(r"\bDM\b", q["architects"], re.I):
        tags.append("ARCHITECTURE")
    if agency_canon(q["agency"]):
        tags.append("AGENT COLLABORATION")
    v = VERIFIED.get(sc)
    if v and v["result"] == "for-sale":
        return "FOR SALE", tags, "verified live listing: " + v["sources"][0]
    if not q["bedrooms"] and not z:
        return "OTHER", tags, "no price or specs"
    return "FEATURED HOME", tags, "sale feature; current availability unverified"


def story(caption):
    """Caption prose before the first dotted separator, minus platform boilerplate."""
    head = re.split(r"\n\s*\.\s*\n", caption)[0]
    keep = []
    for para in re.split(r"\n\s*\n", head):
        p = para.strip()
        if not p or re.search(r"feature your listings|swipe left|drop us a like|follow📲|milestone|followers", p, re.I):
            continue
        p = re.sub(r"[\U0001F300-\U0001FAFF☀-➿️‼❗️⚜️]+", "", p).strip()
        keep.append(p)
    return "\n\n".join(keep)


def media_entries(x):
    out = []
    for m in x["media"]:
        if m["type"] != "image":
            continue
        rel = f"data/raw/media/{x['shortcode']}/{m['index']:02d}.jpg"
        h = HASHES.get(rel)
        if not h or "error" in h:
            continue
        out.append({"src": rel, "w": h["w"], "h": h["h"], "phash": h["phash"], "post": x["shortcode"],
                    "index": m["index"], "alt": None})
    return out


def main():
    by_sc = {x["shortcode"]: x for x in POSTS}
    merged_into = {}
    for group in MERGE:
        for sc in group[1:]:
            merged_into[sc] = group[0]

    classification = []
    groups = defaultdict(list)
    for x in POSTS:
        cat, tags, why = classify(x)
        pid = None
        if cat in ("FOR SALE", "FEATURED HOME", "UNDER OFFER", "SOLD"):
            pid = merged_into.get(x["shortcode"], x["shortcode"])
            groups[pid].append(x)
        classification.append({"shortcode": x["shortcode"], "date": x["date"], "url": x["url"],
                               "category": cat, "tags": tags, "reason": why,
                               "propertyKey": pid})

    agents = {}
    props = []
    for pid, posts in groups.items():
        posts.sort(key=lambda p: p["date"], reverse=True)
        lead = by_sc[pid]
        q = lead["parsed"]
        loc = locate(q["locationLine"] or "") or locate((lead["taggedLocation"] or {}).get("name") or "")
        z = q["prices"].get("ZAR", {})
        v = VERIFIED.get(pid)
        status = "for-sale" if v and v["result"] == "for-sale" else "unknown"
        agency = agency_canon(q["agency"])
        names = contact_names(q["contact"])
        agent_id = None
        if names and agency:
            agent_id = slugify(names[0])
            a = agents.setdefault(agent_id, {"id": agent_id, "name": names[0], "agency": agency,
                                             "coAgents": names[1:], "phone": None, "email": None,
                                             "profileUrl": None, "verified": False,
                                             "credits": [], "sources": []})
            a["credits"].append(pid)
            a["sources"].append(lead["url"])
        images = []
        seen = set()
        for p in posts:
            for m in media_entries(p):
                if m["phash"] in seen:
                    continue
                seen.add(m["phash"])
                images.append(m)
        video = None
        for p in posts:
            if p.get("video") and p["video"].get("url"):
                video = {"src": f"data/raw/media/{p['shortcode']}/00.mp4", "post": p["shortcode"],
                         "durationS": p["video"].get("durationS")}
        architect = q["architects"] if q["architects"] and not re.search(r"\bDM\b", q["architects"], re.I) else None
        beds = q["bedrooms"]
        area = (loc or {}).get("estate") or (loc or {}).get("area") or (loc or {}).get("city") or "South Africa"
        lede = lead["caption"][:260] + " " + " ".join(q["bullets"]) + " " + (q["locationLine"] or "")
        ptype = "Apartment" if re.search(r"apartment|penthouse", lede, re.I) else "House"
        title = f"{int(beds)}-Bedroom {'Penthouse' if 'penthouse' in lede.lower() else ptype}, {area}" if beds else f"Residence, {area}"
        short = re.sub(r"\s+(golf|coastal|residential|nature|eco|private|country|equestrian|signature|security|luxury).*$|\s+estate$", "", area, flags=re.I)
        base_slug = slugify(f"{short}-{int(beds)}-bedroom-{ptype}" if beds else f"{short}-residence")
        prop = {
            "id": pid,
            "slug": base_slug,
            "reference": None,
            "status": status,
            "collection": "for-sale" if status == "for-sale" else "archive",
            "title": title,
            "propertyType": ptype,
            "priceZAR": z.get("amount") if not z.get("poa") and not z.get("perMonth") else None,
            "priceOnApplication": bool(z.get("poa")),
            "priceSourcedAt": lead["date"][:10],
            "foreignPricesAtSource": {k: v.get("amount") for k, v in q["prices"].items() if k != "ZAR" and v.get("amount")},
            "province": (loc or {}).get("province"),
            "city": (loc or {}).get("city"),
            "area": (loc or {}).get("area"),
            "suburb": (loc or {}).get("area"),
            "estate": (loc or {}).get("estate"),
            "development": None,
            "locationLine": q["locationLine"],
            "bedrooms": beds,
            "bathrooms": q["bathrooms"],
            "garages": q["garages"],
            "parking": None,
            "erfSizeM2": q["landM2"],
            "floorSizeM2": q["floorM2"],
            "ratesZAR": None,
            "leviesZAR": None,
            "description": story(lead["caption"]),
            "highlights": [b for b in q["bullets"] if not re.match(r"^\d+(\.\d+)?\s*(\w+\s)?(bed|bath)", b, re.I)][:10],
            "features": features_for(q, lead["caption"], loc),
            "architect": architect,
            "developer": None,
            "images": images,
            "video": video,
            "agentId": agent_id,
            "agentNames": names,
            "agency": agency,
            "agencyRaw": q["agency"],
            "sourceListingUrl": v["sources"][0] if v and v["result"] == "for-sale" else None,
            "instagramPosts": [p["url"] for p in posts],
            "sourceUrls": [p["url"] for p in posts] + (v["sources"] if v else []),
            "firstSeenAt": posts[-1]["date"][:10],
            "lastVerifiedAt": TODAY if v else None,
            "verification": {"result": v["result"], "summary": v["summary"]} if v else None,
            "confidence": "verified-live" if status == "for-sale" else ("checked-not-found" if v else "instagram-only"),
        }
        props.append(prop)

    # verified enrichments for the live listing (from the agency's own page)
    for p in props:
        if p["id"] == "DcjTeOlF_iW":
            p["reference"] = "12LVE 117548729"
            p["parking"] = 4
            p["title"] = "Contemporary Residence, Eye of Africa"
            p["features"] = sorted(set(p["features"]) | {"pool", "solar-backup", "home-automation", "golf-estate", "secure-estate", "entertainment-area"})
            if p["agentId"]:
                a = agents[p["agentId"]]
                a.update({"phone": "078 130 8585", "verified": True,
                          "profileUrl": "https://www.12lve.co.za/property-for-sale-by-gabriel-masilo-a554721",
                          "role": "Principal Property Practitioner"})
                a["sources"].append("https://www.12lve.co.za/4-bedroom-house-for-sale-in-eye-of-africa-estate-117548729")

    # de-duplicate slugs deterministically
    seen = defaultdict(int)
    for p in sorted(props, key=lambda p: (p["status"] != "for-sale", "".join(chr(255 - ord(c)) for c in p["firstSeenAt"]))):
        seen[p["slug"]] += 1
        if seen[p["slug"]] > 1:
            p["slug"] += f"-{seen[p['slug']]}"
    props.sort(key=lambda p: p["firstSeenAt"], reverse=True)
    props.sort(key=lambda p: p["status"] != "for-sale")

    (ROOT / "data/post-classification.json").write_text(json.dumps(classification, ensure_ascii=False, indent=1))
    (ROOT / "data/properties.json").write_text(json.dumps(props, ensure_ascii=False, indent=1))
    (ROOT / "data/agents.json").write_text(json.dumps(sorted(agents.values(), key=lambda a: a["name"]), ensure_ascii=False, indent=1))
    from collections import Counter
    print(Counter(c["category"] for c in classification))
    print(len(props), "properties;", Counter(p["status"] for p in props), ";", len(agents), "credited agents")


if __name__ == "__main__":
    main()
