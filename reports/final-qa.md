# Final QA

Date: 25 September 2026. Build: `./build.sh` output in `docs/` (26 residences: 1 for sale, 25 Portfolio).

## Result

| Check | Result |
|---|---|
| Data and link validator (`scripts/validate.py`) | **0 errors**, 40 warnings (all legitimately missing optional data, below) |
| Functional and responsive suite (`qa/qa.mjs`) | **299/299 passed** |
| Performance (`qa/perf.mjs`, simulated fast 4G) | LCP 0.50 to 0.78 s, **CLS 0** on every measured page, 242 to 489 KB transferred |
| Horizontal overflow | 0 px on all 12 page types at 375, 390, 430, 768, 1024, 1440, 1920 |
| Console / network errors, broken images | None |
| Proposal mode | `noindex, nofollow` on every page, Disallow-all `robots.txt`, no visible "proposal"/"demo" wording (validator-enforced) |

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

## Coverage

**Page types (each at 7 widths: overflow, console/network errors, broken images):** home, collection, Portfolio view, locations, feature your property, about, contact, live agent-credited listing (Eye of Africa), POA listing (Pinnacle Point), limited-data listing (Ballito), architect-credited listing (Waterfall), 404.

**Behaviour:**

| Area | Checks |
|---|---|
| Collection | Defaults to For Sale; For Sale view points to the Portfolio; Portfolio set shows 25 and writes the URL; location (city) filter; price range (R40m+); sort low-high and high-low; feature filter from URL (ocean views); active filter count badge; empty state with a useful route; clear filters |
| URL state | Back restores previous sort; Back restores location without price; Forward re-applies price |
| Home search | Province + bedrooms lands on the filtered collection; location options are generated from inventory (29: province, city and area levels, with an area left out when it repeats its city) |
| Mobile | Menu opens with focus inside and scroll locked, traps focus, Escape restores focus; filters hidden until requested, open as a modal sheet, Apply closes and filters, Escape restores focus |
| Gallery / lightbox | Mobile swipe updates count; lightbox opens, arrow keys forward/back, image loads, focus trapped, body scroll locked, Escape restores focus and scroll, swipe advances |
| Contact | Agent `tel:` is a valid SA number (`+27781308585`); agency listing link present; platform `mailto:` valid; Instagram links point at the account or its posts; "Marketed by" + "Featured by" shown |
| Provenance | POA listing shows price on application; Portfolio pages label availability as unconfirmed and carry no `tel:` links |
| Feature form | Empty submit shows inline error and focuses the first field; valid submit composes a `mailto:` (no backend, no fake system) |
| Accessibility | Reduced motion shows all content; touch targets at least 44px on the mobile property page; first Tab reaches the skip link; visible focus ring on nav |
| Links | Full internal link crawl (validator): no broken links or zero-byte assets |

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
| 5 | Related to Exclusive Cape Town without being a clone? | Yes. It shares dark ground, serif/sans, gold rules and numbered sections. It differs in a cooler blue-black ink, the client's own gold, the two-register For Sale / Portfolio model, sales vocabulary, national location hierarchy and no map. |
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
