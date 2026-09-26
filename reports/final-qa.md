# Final QA

Date: 26 September 2026 (final UX and content pass; first QA 25 September). Build: `docs/` (26 residences: 1 for sale, 25 Portfolio).

## Result

| Check | Result |
|---|---|
| Data and link validator (`scripts/validate.py`) | **0 errors** on every data, provenance, link, image, copy and proposal-mode check; 40 warnings (all legitimately missing optional data, below). The raw-media check needs the gitignored Instagram originals in `data/raw/media/`; where they are absent it lists each one as missing (3,498 entries, identical before and after this pass), so run it where the originals are kept |
| Functional and responsive suite (`qa/qa.mjs`) | **369/369 passed** (299 before this pass; 70 checks added) |
| Performance (`qa/perf.mjs`, simulated fast 4G) | LCP 0.45 to 0.58 s, **CLS 0** on every measured page, 234 to 473 KB transferred |
| Horizontal overflow | 0 px on all 13 page types at 375, 390, 430, 768, 1024, 1440, 1920 |
| Console / network errors, broken images | None |
| Proposal mode | `noindex, nofollow` on every page, Disallow-all `robots.txt`, no visible "proposal"/"demo" wording (validator-enforced) |

## Final UX and content pass (26 September 2026)

Presentation only. No status, price, agent or property fact changed: 1 residence is verified For Sale, 25 remain Portfolio with availability to be confirmed.

### Collection

- **Collection defaults to All Residences: 26 total, comprising 1 verified For Sale and 25 Portfolio residences.** `residences/` shows all 26 with no set parameter; For Sale (`?set=for-sale`, 1) and The Portfolio (`?set=portfolio`, 25) are filters within it. Older `?set=all` links still work and are rewritten to the bare URL.
- Register tabs read **All Residences 26 / For Sale 1 / The Portfolio 25**, All current on first load. Back and Forward restore the register.
- One grid in the curated Recommended order; the live listing ranks first but is not set apart.
- The "25 more residences in the Portfolio" callout is gone; the tabs do that job.
- Intro copy describes one collection with two statuses, and never implies Portfolio homes are available.
- Price sorts read "Price shown, high to low / low to high", because the combined grid mixes a current asking price with historical ones. Sorting still uses the stored figures.
- Location options with no residence in the current register are disabled (For Sale: 26 of 29 disabled; All and Portfolio: none). The option already chosen is never disabled, so a filter is never silently dropped.
- The home search and the location links (home and Locations page) no longer add `set=all`; a search lands on e.g. `residences/?loc=p%3AKwaZulu-Natal&beds=5`.
- "Explore Residences" now opens the full collection (the critique's "one result after Explore" is resolved).

### Cards and prices

One macro, `price_block()` in `src/templates/_macros.html`, renders price and status for `card()` (collection and related residences) and for the homepage Portfolio items, so the treatment cannot drift between views. Status is always stated in words, not colour alone.

| Status | Card treatment |
|---|---|
| For sale | Gold "For sale" flag, title, asking price in gold serif (1.4rem), specs (unchanged) |
| Portfolio, priced | Muted "Previously featured" flag, title, "Asked when featured in April 2023", the published price in smaller muted serif (1.2rem, ivory), "Availability to be confirmed" |
| Portfolio, POA | "Featured in August 2022", "Price on application when featured" (Pinnacle Point, Blue Hills) |
| Portfolio, no figure | "Price not published" (no current residence; nothing is invented) |

- The homepage "From the Portfolio" items gained the same dated price and availability line; the For Sale Now signature keeps its asking price.
- Portfolio property headers use the same vocabulary (POA pages now read "Featured in August 2022 / Price on application when featured").

### Property pages

- **Lower gallery removed.** The second full "Photographs" mosaic is gone. The opening gallery stays: on desktop the main photograph, two supporting photographs and "View all N photographs"; on mobile the swipe strip with its count. Both open the lightbox, which holds every photograph (tested: all 20 for Eye of Africa, each distinct and loadable, reachable with the arrow keys).
- **Financial Details removed.** It repeated the price shown in the header and listed rates and levies as "On request from the agent". No residence has published rates or levies; if one does, they appear in Particulars. None are fabricated.
- Sections renumber without gaps: I Particulars, II The Residence, III Signature Features, then Architecture when credited, then Location (Waterfall runs to V).
- Breadcrumb is **Residences / location**, linking to the whole collection; the page itself states For Sale or Previously featured.
- Pages are shorter and lighter:

| Residence | Height at 1440 | Height at 390 | HTML |
|---|---|---|---|
| Eye of Africa (for sale) | 7,669 to 4,728 px | 9,034 to 6,650 px | 54.1 to 38.2 KB |
| Pinnacle Point (POA) | 6,017 to 4,469 px | 7,241 to 6,130 px | 36.2 to 27.9 KB |
| Ballito (limited data) | 5,648 to 4,194 px | 6,931 to 5,820 px | 34.5 to 26.7 KB |
| Waterfall (architect credit) | 5,927 to 4,631 px | 7,611 to 6,420 px | 34.6 to 27.2 KB |

- Transfer over a full top-to-bottom visit roughly halves (Eye of Africa 1,010 to 496 KB at 1440 and 1,155 to 580 KB at 390; Pinnacle Point 709 to 388 KB at 390), and initial transfer falls slightly (Eye of Africa 489 to 473 KB at 390).

### Navigation

- Footer Explore: **Residences / For sale now / The Portfolio / Locations**. The masthead keeps a single Residences link.

### Regressions found and fixed during the pass

| Issue | Fix |
|---|---|
| At 375 px the longer sort labels pushed the toolbar 3 px past the viewport (8 px into the gutter at 390) | On phones the "Sort" caption sits above its select, as in the search strip |
| With the longer tab labels, "The Portfolio" wrapped onto a row of its own on phones | On phones All Residences takes the first row, with For Sale and The Portfolio beneath it |
| Filtered URLs (e.g. `?loc=p:Gauteng`) scored CLS 0.001 on phones before this pass, 0.002 with the taller sort control: the filter count badge widened the Filters button after load and pushed the sort sideways | At sheet widths (under 980 px) the toolbar spans the row, Filters left and Sort right: CLS 0.000 at every width |
| Breadcrumb link text sat 13 px below the location beside it (present before this pass) | Baseline-aligned |
| Disabling a chosen location option would remove it from the form data and silently clear the filter | The current choice is never disabled (tested) |
| The empty state offered "Search all residences" even when already viewing all | Shown only when another register has matches |

## How to run

```bash
./build.sh                                   # rebuild docs/ and validate
# serve docs/ under the GitHub Pages base path
mkdir -p /tmp/serve && ln -sfn "$PWD/docs" /tmp/serve/Beautiful-South-African-Homes-
(cd /tmp/serve && python3 -m http.server 8321) &
export PW=$(npm root -g)/@playwright/cli/node_modules/playwright   # or any playwright install
node qa/qa.mjs qa/out                         # functional + responsive suite
node qa/perf.mjs                              # LCP / CLS / transfer
node qa/shots.mjs qa/out "" 1440,390 full     # screenshots
```

`BASE` overrides the URL (default `http://localhost:8321/Beautiful-South-African-Homes-/`).

`build.sh` re-encodes images from the Instagram originals, so its image step needs Pillow and `data/raw/media/` (gitignored). Without them, run the other steps directly (`normalize_instagram.py`, `build_data.py`, `build_site.py`, `validate.py`); the committed AVIF/WebP files and `data/image-manifest.json` are used as they are.

## Coverage

**Page types (each at 7 widths: overflow, console/network errors, broken images):** home, collection (All Residences), For Sale view, Portfolio view, locations, feature your property, about, contact, live agent-credited listing (Eye of Africa), POA listing (Pinnacle Point), limited-data listing (Ballito), architect-credited listing (Waterfall), 404.

**Behaviour:**

| Area | Checks |
|---|---|
| Collection | Defaults to All Residences (26 shown: 1 for sale + 25 Portfolio) at the bare URL; All Residences tab current on first load; tabs read All Residences 26 / For Sale 1 / The Portfolio 25 in that order; no Portfolio callout; live listing ranks first in the same grid; sorts labelled "Price shown"; For Sale shows 1 and writes `set=for-sale`; Portfolio shows 25 and writes `set=portfolio`; location options disabled only where the register has nothing (All, For Sale, Portfolio); location (city) filter; price range (R40m+); sort low-high and high-low; feature filter from URL (ocean views); active filter count badge; empty state routes to the whole collection and keeps the chosen location selected; "Search all residences" widens to All and keeps the other filters, and is not offered when already on All; clear filters; a legacy `?set=all` link is rewritten to the canonical URL |
| URL state | Back restores For Sale, then All at the bare URL; Forward re-applies For Sale; the All tab returns to the bare URL; Back restores previous sort; Back restores location without price; Forward re-applies price |
| Home search | Sends no set parameter; province + bedrooms lands on the filtered collection at `?loc=p%3AKwaZulu-Natal&beds=5`; location options are generated from inventory (29: province, city and area levels, with an area left out when it repeats its city) |
| Cards and prices | Collection: the live card says For sale with its current asking price; all 25 Portfolio cards show "Previously featured", a dated "Asked when featured in <month year>" price (or "Price on application when featured"), "Availability to be confirmed", and never "For sale" or "Asking price"; the historical price is smaller and a different colour than the live price. Related residences (Waterfall: live, priced Portfolio and POA; Eye of Africa: Portfolio) and the four homepage Portfolio items follow the same rules; the homepage signature keeps its asking price. Figures are checked against `assets/data/residences.json` |
| Property pages | Eye of Africa, Pinnacle Point, Ballito and Waterfall: section numerals run from I with no gaps; no Photographs or Financial Details section and no "on request" placeholders; breadcrumb is Residences / location, linking to `residences/`. Footer links: Residences, For sale now, The Portfolio, Locations; masthead has no separate For Sale / Portfolio links |
| Mobile | Menu opens with focus inside and scroll locked, traps focus, Escape restores focus; filters hidden until requested, open as a modal sheet, Apply closes and filters, Escape restores focus; call bar waits until the price has scrolled away, reads "Call Gabriel" and does not cover the footer |
| Gallery / lightbox | No lower mosaic; one gallery, with every photograph opener inside it; desktop shows "View all 20 photographs"; the lightbox holds all 20 published photographs (checked against the image files), each distinct and loading; "View all" opens it; arrow keys forward/back and step through all 20, wrapping round; image loads; focus trapped; body scroll locked; Escape restores focus and scroll; swipe advances. Mobile swipe strip holds the same 20 photographs, its count updates and reaches 20 |
| Contact | Agent `tel:` is a valid SA number (`+27781308585`); agency listing link present; platform `mailto:` valid; Instagram links point at the account or its posts; "Marketed by" + "Featured by" shown |
| Provenance | POA listing shows price on application; Portfolio pages label availability as unconfirmed and carry no `tel:` links |
| Feature form | Empty submit shows inline error and focuses the first field; valid submit composes a `mailto:` (no backend, no fake system) |
| Accessibility | Reduced motion shows all content; touch targets at least 44px on the mobile property page; first Tab reaches the skip link; visible focus ring on nav |
| Links | Full internal link crawl (32 URLs) and the validator: no broken links or zero-byte assets |

Screenshots for this pass (`qa/shots.mjs`, full page) cover home, All Residences, For Sale, Portfolio, the live listing and a Portfolio listing at all 7 widths: 0 px overflow and no console errors in all 42.

## Design review fixes (Impeccable critique, 24 Sep 2026: 26/40)

| Priority | Issue | Fix |
|---|---|---|
| P1 | Sticky "Clear all" bar covered the Price filter on desktop | Filter actions are static on desktop |
| P1 | Mobile: agent buried, generic "Call Agent" bar covered the price | Agent name directly under the price; bar reads "Call Gabriel" and reserves its own space |
| P1 | Home led with unavailable Portfolio homes | For Sale Now follows the search; Portfolio comes after, with an availability caveat |
| P2 | Stale Portfolio prices looked current | Muted, smaller, labelled "Asked when featured in <month year>" |
| P2 | Heavy filters, small micro-type, long caps runs | Secondary filters behind "More filters"; micro-type raised (smallest UI text now .7rem); sentence case for longer copy |
| Consistency | Section numerals skipped / started at II | Home folios now run I to VII |
| Brand | Site gold was not the client's gold | Aligned to the logo gold `#BAA360` (CSS and favicon) |
| Perf | CLS 0.169 on the mobile collection page | Fixed (0 now) |

## Design review questions (brief §41)

| # | Question | Answer |
|---|---|---|
| 1 | Does it genuinely feel luxurious? | Yes in structure, pacing and type. The limit is the source photography: most images are 682 px wide and look soft in the large slots on high-DPI screens. Agency originals would fix this. |
| 2 | Is the gold restrained? | Yes. Gold is used only for rules, section numerals, small labels, prices, the focus ring and one primary button per view. It is flat (the client's logo gold `#BAA360`), with no gradients or foil. |
| 3 | Is the serif sophisticated rather than wedding-like? | Mostly. Cormorant is set at weight 400 with lining figures for prices. The critique flagged the gold italic tail as a wedding risk, so italic emphasis is limited to one phrase per heading and the manifesto uses ivory, not gold. |
| 4 | Does photography dominate? | Yes. Every section leads with an image; only the hero caption overlays a photograph. |
| 5 | Related to Exclusive Cape Town without being a clone? | Yes. It shares dark ground, serif/sans, gold rules and numbered sections. It differs in a cooler blue-black ink, the client's own gold, one collection with For Sale and Portfolio statuses, sales vocabulary, national location hierarchy and no map. |
| 6 | Is the sales tone obvious? | Yes: Asking Price, Arrange a Viewing, Marketed by, Property Particulars. No rental or stay vocabulary appears anywhere (checked across `docs/`). |
| 7 | Does it feel national? | Yes. The collection covers Western Cape (12), Gauteng (8), KwaZulu-Natal (5) and Eastern Cape (1), and the hero listing is in Johannesburg. Western Cape is still the largest share, which reflects the account's history. |
| 8 | Does the business model remain accurate? | Yes. The site says it features residences and introduces buyers to the people selling them. It never claims a mandate. "Featured by Beautiful South African Homes" appears on every residence. |
| 9 | Is agent attribution clear? | Yes. The live listing shows "Marketed by Gabriel Masilo, 12LVE Property Group" under the price with a verified number and agency link. Portfolio homes show "Originally marketed by <agency>" with no phone number, because no current contact is verified. |
| 10 | Does mobile keep the luxury character? | Yes. Serif scale, full-width photography, a swipe gallery with a count, a filter sheet, and a sticky "Call Gabriel" bar that reserves its own space. |

## Deliberate deviations from the brief

| Brief | Built | Why |
|---|---|---|
| §18 order: Featured, Collection, then Signature | For Sale Now (Signature) directly after the search, then the Portfolio | The only verified home for sale should come first; the critique flagged leading with unavailable homes (P1) |
| "N° 01" section markers | Roman numerals I to VII; `N°` kept on cards | Keeps a distinct numbering system from Exclusive Cape Town |
| Hero eyebrow and "Explore Properties" | No eyebrow (the wordmark sits above); "Explore Residences" | Avoids repeating the brand name; "Residences" is the site's vocabulary |
| Optional mono face for references | Not used | One reference number did not justify a third font |
| Map | None | Exact addresses are not public, and the location blocks already show the national spread |

## Validator warnings (40, expected)

Missing optional facts on published residences, shown as absent rather than invented: floor size unknown, erf size unknown, garages unknown. Unpublished properties without images are also warned. None block publishing.

## Known limitations

- Source photography is mostly 682 px wide; large slots are soft on high-DPI screens until agencies supply originals.
- `404.html` assumes the `/Beautiful-South-African-Homes-/` base path (`SITE_BASE`); change it with the domain.
- The Portfolio enquiry and the "feature your property" form compose an email; there is no backend, by design.
- Only one residence is verified for sale. Portfolio availability depends on the agency confirming.
- `docs/` is 46 MB (AVIF + WebP for 26 residences).
