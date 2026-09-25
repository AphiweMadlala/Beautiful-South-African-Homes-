# DESIGN.md: Beautiful South African Homes

Dark national residential luxury. A sibling to Exclusive Cape Town (dark coastal hospitality), reinterpreted for **ownership, architecture and national discovery**. Photography leads; type and gold only frame it.

Source of truth: `src/assets/css/site.css` (tokens on `:root`). This document describes what shipped.

## 1. Principles

1. **Photography dominates.** Images are the largest element on every page. Nothing sits on top of a photograph except the live listing's hero caption.
2. **Gold is punctuation.** Only for rules, section numerals, small labels, prices, focus rings and the single primary button. Never used for body text, backgrounds or large fills.
3. **Two registers, always visible.** *For Sale* (verified against the agency's live listing) and *The Portfolio* (previously featured, availability to be confirmed). They never share the same visual weight for price or status.
4. **Restraint in copy.** Factual, short, no superlatives. Property vocabulary (erf, levies, estate) is used plainly.
5. **Sales, not stays.** CTAs lead to the marketing agent or agency, never to a booking flow.

### How it differs from Exclusive Cape Town

| Exclusive Cape Town | Beautiful South African Homes |
|---|---|
| Villa escapes, per-night rates | Residences to own, asking prices in ZAR |
| Cape-coast imagery | Four provinces: coast, winelands, Highveld |
| Hospitality enquiry | Agent and agency attribution ("Marketed by / Featured by") |
| Single-register inventory | For Sale vs The Portfolio registers |
| Warm-black ground | Cooler blue-black ink (`#0B0F14`) with the client's own logo gold |

## 2. Colour

| Token | Value | Use | Contrast on ink |
|---|---|---|---|
| `--ink` | `#0B0F14` | Page background | |
| `--ink-2` | `#0F141B` | Alternate band | |
| `--surface` | `#131A22` | Image placeholders, cards, sheets | |
| `--raised` | `#1A222C` | Menus, lightbox chrome | |
| `--ivory` | `#F1ECE2` | Primary text, headings | 16+:1 |
| `--ivory-2` | `#B9B2A6` | Secondary text, ledes | 9.1:1 |
| `--ivory-3` | `#8E887E` | Tertiary text, small labels | 5.4:1 |
| `--gold` | `#BAA360` | Accent text and detail. Sampled from the client's logo | 7.8:1 |
| `--gold-deep` | `#8A7743` | Rules and borders only, never text | |
| `--line` | ivory @ 12% | Hairlines | |
| `--line-strong` | ivory @ 24% | Input and chip borders | |
| `--line-gold` | gold @ 38% | Underlines on links and secondary buttons | |

`color-scheme: dark`; `theme-color` is `#0B0F14`. The site is dark only by design (no light theme).

## 3. Typography

Self-hosted variable WOFF2 (`src/assets/fonts/`), `font-display: swap`.

| Role | Family | Details |
|---|---|---|
| Display, titles, prices, numerals | **Cormorant Garamond** 400, italic for emphasis | `line-height: 1.08`, `text-wrap: balance`, slight negative tracking |
| Body, UI, labels | **Jost** 400/500 | Body `1rem/1.7` |
| Small caps labels (`.k`) | Jost 500 | `.72rem`, `letter-spacing: .2em`, uppercase, `--ivory-3` |

- Section heading: `clamp(2.2rem, 4.6vw, 3.9rem)`, max 18ch.
- Lede: `clamp(1.02rem, 1.3vw, 1.14rem)`, `--ivory-2`, max 58ch.
- `em` inside `.display` turns gold italic. Use at most once per heading (the manifesto uses ivory-2 instead to keep gold rare).
- Prices, specs and counts use `lining-nums tabular-nums`; Cormorant defaults to old-style figures.
- Minimum UI text is `.7rem` (wordmark line), and uppercase is limited to short labels. Longer runs use sentence case.

## 4. Wordmark

Typographic, not a redrawn logo: *Beautiful* in Cormorant italic (ivory, 1.32rem) over **SOUTH AFRICAN HOMES** in Jost caps (gold, `.7rem`, tracking `.34em`). The client's gold geometric monogram should be placed beside it once a vector original is supplied. The favicon is an italic gold *B* on ink with a gold-deep rule.

## 5. Layout

- `--max: 1400px`, `--gutter: clamp(1.25rem, 4vw, 3.5rem)`, `--nav-h: 72px`.
- `.section` padding: `clamp(4.5rem, 10vw, 9rem)` vertical.
- Breakpoints (max-width): 480, 699, 767, 899 (main layout switch), 979 (collection filters become a sheet); 1180+ for wide refinements.
- Image ratios: cards and mosaic 3:2, featured tall card 4:5, locations 16:10, mobile gallery 4:3. Every media box has `background: var(--surface)` and a fixed ratio, so there is no layout shift (CLS 0 on all measured pages).

### Folio (numbered section marker)

Gold italic roman numeral, a 3rem gold-deep rule that grows in on reveal, and a small caps label. The home page runs I to VII: Platform, For Sale Now, From the Portfolio, The Collection, Locations, Feature Your Property, Contact. The hero has no numeral.

## 6. Components

| Component | Notes |
|---|---|
| Nav | Transparent over the hero, turns solid ink once the hero leaves view. Links: `.74rem` tracked caps; gold underline scales in from the left. Mobile: full-screen menu, serif links, focus trapped, Escape closes. |
| Hero | Near full-bleed image on the right, copy on ink on the left, caption crediting location and agency. |
| Search strip | Location, price, bedrooms, type then a gold **Search** button. Lands on `residences/` with URL state. |
| Signature (For Sale Now) | Large image plus a spec panel: estate, title, asking price in gold serif, bedrooms, bathrooms, garages, "Marketed by" agent and agency. |
| Card | 3:2 image, `N°` folio number, location, serif title, price. Portfolio cards show a muted, smaller price labelled "Asked when featured" with the month it was featured. |
| Registers | Tabs **For Sale / The Portfolio / All** with italic gold counts. Default view is For Sale. |
| Filters | Desktop: static left rail (location, type chips, price, bedrooms), with the rest behind "More filters". Mobile (<980px): button with an active count opens a modal sheet. |
| Property page | Title and price, then agent name directly under the price on mobile, specs, story, signature features (gold-rule bullets), photography mosaic, financial details, location, "Arrange a Viewing" panel. Mobile has a sticky call bar ("Call Gabriel") that reserves its own space. |
| Portfolio property page | No `tel:` links. Availability stated as unconfirmed; enquiry is a composed email. |
| Gallery and lightbox | Mosaic (every fifth tile spans 2×2); mobile swipe track with a count; lightbox with arrows, swipe, focus trap, scroll lock and Escape. |
| Buttons | `.btn-gold` (one primary per view), `.btn-line` (gold hairline), `.btn-sm` (44px). All at least 48px tall, `.78rem` tracked caps. |

### CTA vocabulary

- For sale: **Call Gabriel** / **Call 078 130 8585**, **View Agency Listing**.
- Portfolio: **Ask About This Residence** (mailto).
- Discovery: **Explore Residences**, **View Residence**.
- Supply: **Submit a Residence** / **Feature a Property**.

## 7. Motion

- One easing curve: `--ease: cubic-bezier(.16, 1, .3, 1)`.
- Reveal: fade plus 18px rise (1s); images settle from `scale(1.06)` (1.8s); folio rules grow in. All driven by IntersectionObserver, and only under `prefers-reduced-motion: no-preference`.
- Hover: image zoom over 1.2 to 1.4s, underline scale over .5s, colour over .3s.
- Reduced motion: all content visible and transitions near zero (tested).

## 8. Accessibility

- Skip link, visible 2px gold focus ring (`outline-offset: 3px`), `:focus-visible` only.
- Touch targets at least 44px (tested on mobile property pages).
- Menus, filter sheet and lightbox trap focus, lock scroll and restore focus on Escape.
- Text contrast is at least 5.4:1 everywhere; gold-deep is never used for text.

## 9. Photography

- Source images are mostly 682px wide Instagram exports. Layouts cap the rendered width of most tiles; large hero and signature slots need agency originals before launch.
- Served as AVIF with WebP fallback from `src/assets/img/<property>/`, generated by `scripts/build_images.py`.
- Only photographs from the property's own posts are used. No stock or unrelated imagery.

## 10. Do / Don't

**Do:** let one photograph carry each section · keep gold under roughly 5% of any viewport · show dates beside any price that isn't live · credit the agency on every residence.

**Don't:** put gold on large areas · use superlatives or "dream home" copy · show a Portfolio price at live-price weight · add booking or enquiry backends · use the ⚜️ emoji or crest motifs.
