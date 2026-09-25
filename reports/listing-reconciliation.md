# Listing Reconciliation

380 posts -> 366 sale-feature posts -> **362 unique properties**.

## Deduplication method

1. **Perceptual hashing** of all 3,544 downloaded images (`data/raw/media-hashes.json`, pHash). Any two posts sharing images within Hamming distance 8 were reviewed.
2. **Metadata grouping** by normalised location + bedrooms + bathrooms, then compared on price, agency, garages and land size, and re-checked with a looser image threshold (distance <= 12). Every such pair scored >= 20 (unrelated), so none were merged on metadata alone.
3. **Identical captions** on the same day (reel + carousel of one home).

## Merged (one property, several posts)

| Property | Posts | Evidence |
|---|---|---|
| 5-Bedroom House, Meyersdal (`CZ4aN__MjG5`) | CZ4dEfeldVR, CZ4aN__MjG5 | reel + carousel, same day, identical caption |
| 6-Bedroom House, Zimbali Coastal Resort & Estate (`Cfmb7H5j3IP`) | Cfmb7H5j3IP, CXDuVM6M1lu | 3 shared images; same 2 687 m2 stand, Pam Golding both times |
| 9-Bedroom House, Hout Bay (`CbLGu49sIPo`) | CbLGu49sIPo, COybHiZDNrI | 3 shared images; Tyson Properties both times; 2021 R36m |
| 6-Bedroom House, Waterfall Equestrian Estate (`CaKg6gkMDhc`) | CaKg6gkMDhc, CFPzw5HpYLy | 3 shared images; 2020 feature R69m, 2022 feature (price not stated) |

## Compilation posts (not properties)

CEPdh9WpuTE, CDE1PKoJFlY, CCwS-MnJTy9 reuse single images from other features (kitchens / entertaining). CH3EBygJlL2 reuses an image from CHs4jk6n5XX (St Francis Bay). Classified EDITORIAL / BRAND CONTENT.

## Near-misses kept separate

- Steyn City 4-bed at R29 995 000 posted 2020 (CAfXraYJ-Xu) and 2022 (CeWPKkZjjVT): same price and bed count, but image distance >= 20 across all images; kept separate and noted as a possible relisting with new photography.
- Zimbali 4-bed at R19 700 000 (Cah8irEslSc, Feb 2022) vs today's Seeff P24-117247114 at the same price: different specs; unconfirmed (see listing-provenance.md).

## Status after reconciliation

| Status | Properties |
|---|---|
| for-sale | 1 |
| unknown | 361 |

`unknown` means Instagram-only evidence, or checked and not found live. It is never shown as For Sale.
