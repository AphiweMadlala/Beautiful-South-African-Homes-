#!/usr/bin/env python3
"""Perceptual-hash every downloaded image -> data/raw/media-hashes.json (for dedup + reconciliation)."""
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import imagehash
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
def h(p):
    try:
        with Image.open(p) as im:
            return str(p.relative_to(ROOT)), {"phash": str(imagehash.phash(im)), "w": im.width, "h": im.height, "bytes": p.stat().st_size}
    except Exception as e:  # noqa: BLE001
        return str(p.relative_to(ROOT)), {"error": str(e)}
if __name__ == "__main__":
    files = sorted((ROOT / "data/raw/media").glob("*/*.jpg"))
    with ProcessPoolExecutor() as ex:
        out = dict(ex.map(h, files, chunksize=32))
    (ROOT / "data/raw/media-hashes.json").write_text(json.dumps(out, indent=0))
    print(len(out), "hashed;", sum("error" in v for v in out.values()), "errors")
