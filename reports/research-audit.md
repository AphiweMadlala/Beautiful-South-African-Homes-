# Research Audit

Date: 24 September 2026. Environment: GitHub Codespaces.

## Tools

| Tool | Status | How it was used |
|---|---|---|
| Apify | Used (token-based REST API; `apify` CLI 1.10.0 present but not logged in, OAuth avoided per brief) | `instagram-profile-scraper` (profile + 2 related profiles), `instagram-scraper` (all 380 posts, full carousels), `rag-web-browser` (agency/portal pages, JS-rendered). Free plan: $5/month cap; ~$2.43 used before this project, marginal spend here under $0.10. Concurrency above 2 runs returns HTTP 402 (memory cap), so `scripts/webfetch.py` runs 2 at a time. |
| Firecrawl | **Unavailable** | CLI 1.24.4 installed but not authenticated and `FIRECRAWL_API_KEY` unset. Substituted by Apify `rag-web-browser` for page extraction and the built-in web search for discovery. |
| Agent Reach | **Unavailable** | Only the skill documentation is installed; the `agent-reach` CLI is not. Not installed (would pull unreviewed code from a GitHub `main` zip without the user's go-ahead). Agent and business verification done with web search, agency sites and Instagram profile data. |
| Playwright | Used | Chromium installed (plus system dependencies via Playwright's `install-deps`). `qa/qa.mjs` suite and screenshots. |
| design-taste-frontend, Impeccable | Used | Design direction, critique, audit, polish. |
| design-md | Referenced for DESIGN.md structure. |

## Instagram extraction

- 380 of 380 posts (entire feed): `data/raw/instagram-posts-raw.json` (Apify dataset dTGB3GLh2oUfehPLB).
- Normalised to `data/instagram-posts.json`: id, shortcode, URL, date, caption, media type, product type, carousel media in order (with per-item dimensions), video URL/duration/views, cover, author, collaborators (coauthors), tagged users, tagged location, hashtags, mentions, alt text, likes/comments, and parsed caption fields (location line, contact, agency, architects, photographer, bullets, beds/baths/garages, land/floor m2, ZAR/USD/EUR/GBP prices, rental flag).
- Media downloaded immediately because Instagram CDN URLs expire.

## Web verification

Scope decision: the feed is dormant (364 of 380 posts date from 2019-2022). Verification effort went to the 15 most recent features (2023-2026) plus opportunistic matches, because a 2020-2022 luxury listing is very unlikely to still be live at the same price. Results in `data/verification.json`:

| Outcome | Count |
|---|---|
| Verified live for sale | 1 (Eye of Africa, 12LVE, R9m) |
| Removed from Property24 | 1 (Steyn City, Rawson, R29m) |
| Not among the credited agent's current listings | 5 |
| Same price/estate found but specs differ (unconfirmed) | 2 (Zimbali R19.7m; Meyersdal R17.99m) |
| Only third-party reposts found | 1 (Waterfall Equestrian, Karel Keuler) |

Everything else is `unknown` and appears only in the Portfolio, labelled as such.

## Limits and risks

- Property24 and Private Property statuses were read from public pages at one point in time. A 404 or absence is evidence of "not listed there", not proof of sale.
- Agent contact details are published only where the agency's own listing page shows them (one agent).
- Web search summaries were never used as evidence on their own; every status is backed by a fetched page stored in `data/raw/web/`.
- Exchange rates: foreign prices are shown only for the live listing, as published on 27 Aug 2026 and labelled with that date. No live FX workflow exists, so none is calculated.
