#!/usr/bin/env python3
"""Fetch pages (or run web searches) through Apify's rag-web-browser using APIFY_TOKEN.

Usage: webfetch.py <name> <url-or-query> [<name> <url-or-query> ...]
Saves data/raw/web/<name>.md (markdown) and <name>.json (raw result, incl. HTTP status).
Runs requests concurrently. Token is read from the environment and never printed.
"""
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data/raw/web"
OUT.mkdir(parents=True, exist_ok=True)
API = "https://api.apify.com/v2/acts/apify~rag-web-browser/run-sync-get-dataset-items?timeout=240"


def run(name, query):
    body = json.dumps({"query": query, "maxResults": 3 if not query.startswith("http") else 1,
                       "outputFormats": ["markdown"]}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": "Bearer " + os.environ["APIFY_TOKEN"], "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.load(r)
    except Exception as e:  # noqa: BLE001
        return f"{name}: ERROR {e}"
    (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    md = []
    for item in data:
        crawl = item.get("crawl", {})
        meta = item.get("metadata", {})
        md.append(f"<!-- url: {meta.get('url')} status: {crawl.get('httpStatusCode')} -->\n"
                  f"# {meta.get('title')}\n\n{item.get('markdown', '')}")
    (OUT / f"{name}.md").write_text("\n\n---\n\n".join(md))
    return f"{name}: {len(data)} result(s) " + ", ".join(
        str(i.get('crawl', {}).get('httpStatusCode')) for i in data)


if __name__ == "__main__":
    args = sys.argv[1:]
    pairs = list(zip(args[::2], args[1::2]))
    with ThreadPoolExecutor(max_workers=2) as ex:
        for line in ex.map(lambda p: run(*p), pairs):
            print(line)
