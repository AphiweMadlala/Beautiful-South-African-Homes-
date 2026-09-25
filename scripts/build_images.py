#!/usr/bin/env python3
"""Encode published property images to AVIF + WebP at 640w and native width (max 1600, never upscaled).

Publishes: the verified for-sale set + data/curation.json (the Portfolio).
Output:    src/assets/img/<slug>/<nn>-<w>.{avif,webp}  and data/image-manifest.json
Skips files that already exist, so re-runs are cheap.
"""
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src/assets/img"
SMALL, MAX = 640, 1600


def published():
    props = json.loads((ROOT / "data/properties.json").read_text())
    cur = set(json.loads((ROOT / "data/curation.json").read_text()))
    return [p for p in props if p["status"] == "for-sale" or p["id"] in cur]


def encode(job):
    src, dest_base = job
    im = ImageOps.exif_transpose(Image.open(ROOT / src)).convert("RGB")
    out = {"w": im.width, "h": im.height, "variants": []}
    for target in sorted({min(SMALL, im.width), min(MAX, im.width)}):
        h = round(im.height * target / im.width)
        v = im if target == im.width else im.resize((target, h), Image.LANCZOS)
        for fmt, kw in (("avif", {"quality": 58, "speed": 6}), ("webp", {"quality": 78, "method": 5})):
            p = dest_base.with_name(f"{dest_base.name}-{target}.{fmt}")
            if not p.exists() or p.stat().st_size == 0:
                v.save(p, fmt.upper(), **kw)
            out["variants"].append({"w": target, "h": h, "fmt": fmt,
                                    "path": str(p.relative_to(ROOT / "src")), "bytes": p.stat().st_size})
    return src, out


def main():
    jobs = []
    for p in published():
        d = OUT / p["slug"]
        d.mkdir(parents=True, exist_ok=True)
        for i, img in enumerate(p["images"]):
            jobs.append((img["src"], d / f"{i:02d}"))
    with ProcessPoolExecutor() as ex:
        manifest = dict(ex.map(encode, jobs, chunksize=4))
    (ROOT / "data/image-manifest.json").write_text(json.dumps(manifest, indent=0))
    total = sum(v["bytes"] for m in manifest.values() for v in m["variants"])
    print(f"{len(manifest)} images, {total / 1e6:.1f} MB encoded")


if __name__ == "__main__":
    main()
