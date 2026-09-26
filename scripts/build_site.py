#!/usr/bin/env python3
"""Build the static site: src/ templates + data/ -> docs/ (GitHub Pages ready).

PROPOSAL_MODE adds noindex/nofollow and a Disallow-all robots.txt. Nothing on the page says "proposal".
All links are relative so the site works under any base path.
"""
import json
import re
import shutil
from collections import Counter, OrderedDict, defaultdict
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

PROPOSAL_MODE = True
# 404.html is served at any depth by GitHub Pages, so it alone uses an absolute base.
SITE_BASE = "/Beautiful-South-African-Homes-/"

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "docs"

BRAND = {
    "name": "Beautiful South African Homes",
    "email": "beautifulsahomes@gmail.com",
    "instagram": "https://www.instagram.com/beautifulsouthafricanhomes/",
    "instagramHandle": "@beautifulsouthafricanhomes",
    "followers": "28,600",
    "since": 2019,
}

FEATURE_LABEL = {
    "pool": "Swimming pool", "ocean-views": "Ocean views", "golf-estate": "Golf estate",
    "home-gym": "Private gym", "cinema": "Cinema room", "wine-cellar": "Wine cellar",
    "home-automation": "Home automation", "solar-backup": "Solar and backup power",
    "flatlet": "Guest flatlet", "elevator": "Residential lift", "equestrian": "Equestrian",
    "entertainment-area": "Entertainment areas", "mountain-views": "Mountain views",
    "secure-estate": "Secure estate", "large-garaging": "Garaging for four or more",
    "large-stand": "Stand over 2,000 m²",
}

PROVINCE_ORDER = ["Western Cape", "Gauteng", "KwaZulu-Natal", "Eastern Cape", "North West"]
MONTHS = "January February March April May June July August September October November December".split()

# Alt text for the verified listing, written from the photographs themselves.
LIVE_ALT = [
    "The residence at dusk, seen from above among neighbouring homes in the estate",
    "Street facade with double garage and landscaped verge",
    "Double-volume entrance hall with open staircase",
    "Kitchen with marble-topped centre island",
    "Open-plan kitchen and dining area",
    "Dining room opening onto the kitchen",
    "Family lounge with feature screen",
    "Upstairs lounge behind a glass balustrade",
    "Enclosed entertainment lounge opening to the view",
    "Entertainment lounge with built-in braai",
    "Rear facade and swimming pool at dusk",
    "Swimming pool and rear facade lit at dusk",
    "Pool terrace and outdoor dining at dusk",
    "The home and pool on its hillside stand, from above",
    "Eye of Africa estate: the golf course at sunset",
    "Eye of Africa estate: on the championship course",
    "Eye of Africa estate: the residents' gym",
    "Eye of Africa estate: a walking trail at sunset",
    "Eye of Africa estate: sports and padel courts at dusk",
    "Eye of Africa estate: the clubhouse terrace",
]
LIVE_ESTATE_FROM = 14  # images 14+ show estate amenities, not the house
LIVE_STORY = [
    "Designed for family living and easy entertaining, this contemporary home pairs bold architecture with generous living spaces and a true indoor-outdoor lifestyle.",
    "A double-volume entrance leads to a finished kitchen with centre island and a separate scullery, an enclosed entertainment lounge and an expansive patio above a private pool. Upstairs, balconies take in elevated views across the estate.",
]
LIVE_LOCATION_NOTE = ("Eye of Africa is one of Johannesburg South's premier residential estates, set around the "
                      "Greg Norman Signature Championship Golf Course, with walking and cycling trails, tennis, "
                      "padel, a residents' gym, restaurants and a secure, family-focused environment.")

# Short lede per portfolio home. Composed only from facts in the original feature.
FEATURED_ORDER = ["Cn2JtKsNrkR", "CnUm7GTNQwT", "CrJbjU8ttlW", "Co7yc0et5AH"]
SIGNATURE_ID = "DcjTeOlF_iW"


def fmt_zar(n):
    return "R " + f"{n:,}".replace(",", " ")


def fmt_short(n):
    if n >= 1_000_000:
        v = n / 1_000_000
        return f"R{v:.1f}m".replace(".0m", "m") if v < 100 else f"R{v:.0f}m"
    return fmt_zar(n)


def num(x):
    if x is None:
        return None
    return int(x) if float(x).is_integer() else x


def month_year(iso):
    y, m, _ = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def lede(p):
    beds = num(p["bedrooms"])
    place = p["estate"] or p["area"] or p["city"]
    where = f"{place}, {p['city']}" if p["city"] and p["city"] not in (place or "") else place
    kind = "penthouse" if "Penthouse" in p["title"] else ("apartment" if p["propertyType"] == "Apartment" else "residence")
    bits = [f"A {beds}-bedroom {kind} in {where}"]
    extras = []
    if p["erfSizeM2"]:
        extras.append(f"set on {p['erfSizeM2']:,} m²")
    if extras:
        bits.append(", " + ", ".join(extras))
    s = "".join(bits) + "."
    if p["architect"] and not p["architect"].startswith("@"):
        s += f" Designed by {p['architect']}."
    return s


def picture_data(p, manifest, i, img):
    m = manifest[img["src"]]
    var = m["variants"]
    by = defaultdict(list)
    for v in var:
        by[v["fmt"]].append(v)
    large = max(var, key=lambda v: v["w"])
    return {
        "avif": ", ".join(f"{v['path']} {v['w']}w" for v in sorted(by["avif"], key=lambda v: v["w"])),
        "webp": ", ".join(f"{v['path']} {v['w']}w" for v in sorted(by["webp"], key=lambda v: v["w"])),
        "fallback": [v for v in by["webp"] if v["w"] == large["w"]][0]["path"],
        "small": min(by["webp"], key=lambda v: v["w"])["path"],
        "w": m["w"], "h": m["h"],
        "alt": img.get("alt") or f"{p['title']}, photograph {i + 1} of {len(p['images'])}",
        "estate": img.get("estate", False),
    }


WORDS = "Zero One Two Three Four Five Six Seven Eight Nine Ten".split()


def editorial_title(p):
    if p["id"] == SIGNATURE_ID:
        return p["title"]
    m = re.match(r"(\d+)-Bedroom (\w+), (.+)", p["title"])
    if not m:
        return p["title"]
    n, kind, place = int(m.group(1)), m.group(2), m.group(3)
    kind = {"House": "Residence"}.get(kind, kind)
    return f"{WORDS[n] if n < len(WORDS) else n}-Bedroom {kind}, {place}"


def site_property(p, manifest, agents):
    live = p["status"] == "for-sale"
    p = {**p, "title": editorial_title(p)}
    if p["id"] == SIGNATURE_ID:
        for i, img in enumerate(p["images"]):
            img["alt"] = LIVE_ALT[i]
            img["estate"] = i >= LIVE_ESTATE_FROM
    pics = [picture_data(p, manifest, i, img) for i, img in enumerate(p["images"])]
    cover_index = 10 if p["id"] == SIGNATURE_ID else 0
    agent = dict(agents[p["agentId"]]) if live and p["agentId"] else None
    if agent and agent.get("phone"):
        digits = re.sub(r"\D", "", agent["phone"])
        agent["tel"] = "+27" + digits[1:] if digits.startswith("0") else "+" + digits
        agent["first"] = agent["name"].split()[0]
    place = p["estate"] or p["area"]
    specs = OrderedDict()
    for label, key, unit in (("Bedrooms", "bedrooms", ""), ("Bathrooms", "bathrooms", ""),
                             ("Garages", "garages", ""), ("Parking", "parking", ""),
                             ("Floor", "floorSizeM2", " m²"), ("Erf", "erfSizeM2", " m²")):
        v = num(p.get(key))
        if v is not None:
            specs[label] = f"{v:,}{unit}" if isinstance(v, int) and v >= 1000 else f"{v}{unit}"
    if p["priceOnApplication"]:
        price_label, price_short, price_value = "Price on application", "POA", None
    elif p["priceZAR"]:
        price_label, price_short, price_value = fmt_zar(p["priceZAR"]), fmt_short(p["priceZAR"]), p["priceZAR"]
    else:
        price_label, price_short, price_value = "Price on request", "On request", None
    foreign = None
    if live and p["foreignPricesAtSource"]:
        sym = {"USD": "US$", "EUR": "€", "GBP": "£"}
        foreign = {"date": f"{int(p['priceSourcedAt'][8:])} {month_year(p['priceSourcedAt'])}",
                   "values": [f"{sym[k]}{v:,}" for k, v in p["foreignPricesAtSource"].items()]}
    return {
        "id": p["id"], "slug": p["slug"], "live": live,
        "title": p["title"], "place": place, "type": p["propertyType"],
        "province": p["province"], "city": p["city"], "area": p["area"], "estate": p["estate"],
        "locationLine": ", ".join(x for x in OrderedDict.fromkeys([place, p["city"], p["province"]]) if x),
        "shortLocation": ", ".join(x for x in OrderedDict.fromkeys([place, p["city"]]) if x),
        "bedrooms": num(p["bedrooms"]), "bathrooms": num(p["bathrooms"]), "garages": num(p["garages"]),
        "specs": specs, "priceLabel": price_label, "priceShort": price_short, "price": price_value,
        "poa": p["priceOnApplication"], "foreign": foreign,
        # shown in Particulars only when published; never "on request" placeholders
        "financials": [(label, fmt_zar(v)) for label, v in (("Rates and taxes", p["ratesZAR"]), ("Levies", p["leviesZAR"])) if v],
        "featuredWhen": month_year(p["firstSeenAt"]),
        "features": [FEATURE_LABEL[f] for f in p["features"] if f in FEATURE_LABEL],
        "featureKeys": p["features"],
        "highlights": [h.rstrip(".") for h in p["highlights"]],
        "story": LIVE_STORY if p["id"] == SIGNATURE_ID else [lede(p)],
        "locationNote": LIVE_LOCATION_NOTE if p["id"] == SIGNATURE_ID else None,
        "architect": p["architect"],
        "agency": p["agency"], "agent": agent,
        "listingUrl": p["sourceListingUrl"], "reference": p["reference"],
        "instagram": p["instagramPosts"][0],
        "pictures": pics, "cover": pics[cover_index],
        "houseCount": sum(1 for x in pics if not x["estate"]),
    }


def location_tree(props):
    tree = OrderedDict()
    for prov in PROVINCE_ORDER:
        ps = [p for p in props if p["province"] == prov]
        if not ps:
            continue
        cities = OrderedDict()
        for city, n in Counter(p["city"] for p in ps).most_common():
            areas = Counter(p["place"] for p in ps if p["city"] == city and p["place"] != city)  # the city option already covers these
            cities[city] = {"count": n, "areas": sorted(areas.items())}
        tree[prov] = {"count": len(ps), "cities": cities}
    return tree


def rel(depth):
    return "../" * depth


def main():
    props_all = json.loads((ROOT / "data/properties.json").read_text())
    curation = json.loads((ROOT / "data/curation.json").read_text())
    agents = {a["id"]: a for a in json.loads((ROOT / "data/agents.json").read_text())}
    manifest = json.loads((ROOT / "data/image-manifest.json").read_text())

    by_id = {p["id"]: p for p in props_all}
    ordered = [p for p in props_all if p["status"] == "for-sale"] + [by_id[i] for i in curation]
    props = [site_property(p, manifest, agents) for p in ordered]
    # public slugs: drop the internal dedup counter; disambiguate real collisions by feature year
    base = Counter(re.sub(r"-\d+$", "", p["slug"]) for p in props)
    for p, src in zip(props, ordered):
        b = re.sub(r"-\d+$", "", p["slug"])
        p["slug"] = b if base[b] == 1 else f"{b}-{src['firstSeenAt'][:4]}"
    assert len({p["slug"] for p in props}) == len(props), "duplicate public slugs"
    for i, p in enumerate(props):
        p["rank"] = i
        p["folio"] = f"{i + 1:02d}"
    sp = {p["id"]: p for p in props}
    for_sale = [p for p in props if p["live"]]
    portfolio = [p for p in props if not p["live"]]
    tree = location_tree(props)
    features_present = [(k, FEATURE_LABEL[k], n) for k, n in Counter(
        f for p in props for f in p["featureKeys"]).most_common() if n >= 2 and k in FEATURE_LABEL]

    # province imagery for the Locations blocks: pick the strongest landscape image per province
    PROVINCE_PICK = {"Western Cape": "CfCa7afDfti", "Gauteng": "Co7yc0et5AH", "KwaZulu-Natal": "CYPQYRFs4tk"}
    province_image = {prov: sp[i]["cover"] for prov, i in PROVINCE_PICK.items() if i in sp}
    for prov in tree:
        if prov in province_image:
            continue
        cands = [p for p in props if p["province"] == prov]
        cands.sort(key=lambda p: (not p["live"], -p["cover"]["w"]))
        province_image[prov] = cands[0]["cover"]

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC / "assets", OUT / "assets")

    env = Environment(loader=FileSystemLoader(SRC / "templates"), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters["slug"] = lambda s: re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    common = dict(brand=BRAND, proposal=PROPOSAL_MODE, year=date.today().year, tree=tree,
                  for_sale=for_sale, portfolio=portfolio, props=props, features=features_present,
                  total_featured=sum(1 for p in props_all), agencies=len({p["agency"] for p in props_all if p["agency"]}))

    def render(tpl, path, depth, root=None, **kw):
        dest = OUT / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        html = env.get_template(tpl).render(root=rel(depth) if root is None else root, depth=depth, page=path, **common, **kw)
        dest.write_text(html)

    render("index.html", "index.html", 0, signature=sp[SIGNATURE_ID],
           featured=[sp[i] for i in FEATURED_ORDER], province_image=province_image)
    render("collection.html", "residences/index.html", 1)
    for p in props:
        related = [q for q in props if q is not p and q["province"] == p["province"]][:3]
        if len(related) < 3:
            related += [q for q in props if q is not p and q not in related][: 3 - len(related)]
        render("property.html", f"residences/{p['slug']}/index.html", 2, p=p, related=related)
    render("locations.html", "locations/index.html", 1, province_image=province_image)
    render("feature.html", "feature-your-property/index.html", 1)
    render("about.html", "about/index.html", 1)
    render("contact.html", "contact/index.html", 1)
    render("404.html", "404.html", 0, root=SITE_BASE)

    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n" if PROPOSAL_MODE else "User-agent: *\nAllow: /\n")
    (OUT / ".nojekyll").write_text("")
    # slim client data for filters (the cards themselves are server-rendered)
    (OUT / "assets/data").mkdir(parents=True, exist_ok=True)
    (OUT / "assets/data/residences.json").write_text(json.dumps([{
        "slug": p["slug"], "live": p["live"], "province": p["province"], "city": p["city"], "place": p["place"],
        "type": p["type"], "price": p["price"], "beds": p["bedrooms"], "baths": p["bathrooms"],
        "garages": p["garages"], "features": p["featureKeys"], "rank": p["rank"]} for p in props]))
    print(f"built {len(props)} residences ({len(for_sale)} for sale, {len(portfolio)} portfolio) -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
