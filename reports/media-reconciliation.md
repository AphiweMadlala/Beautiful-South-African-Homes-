# Media Reconciliation

## Inventory

- Posts: 380; media items referenced: 3 558 (3 554 images + 4 videos).
- Downloaded: 3544 images, 4 videos (`data/raw/media/<shortcode>/NN.jpg|mp4`, not committed: 389 MB).
- Failed: all 10 images of CZR_ohysFa9 (Jan 2022, Eye of Africa) returned CDN errors. Property kept with no images; not published.
- Zero-byte files: 0. Decode errors: 0.

## Resolution (the key constraint)

| Width | Images |
|---|---|
| <800 | 3057 |
| 800-999 | 53 |
| 1000-1399 | 429 |
| >=1400 | 5 |

Instagram reports `originalWidth` 682 for most carousels: the account uploaded low-resolution images, so no higher-resolution copy exists on Instagram. Consequences for the design:
- Hero uses the live listing's 1 152 px dusk image in a near-full-bleed 62% column rather than a 1 920 px full bleed.
- Portfolio cards and mosaics are sized so 683 px sources are not stretched far beyond native width; the lightbox caps upscaling at 1.6x.
- **Client action:** request original photography from the agencies for any residence that will be promoted.

## Duplicates

- Cross-post duplicates resolved by pHash (see listing-reconciliation.md). Within a merged property, duplicate images are dropped by hash.
- Validation fails the build if two properties share an identical gallery (none do).

## Published media

- 273 images across 26 residences, encoded to AVIF + WebP at 640 w and native width (max 1 600, never upscaled): 43.7 MB total.
- Every `<img>` has explicit width/height, lazy loading below the fold, `fetchpriority=high` on the LCP image.
- Live listing images 14-19 show estate amenities (golf course, gym, trails, courts, clubhouse), not the house. They are grouped under 'The estate' in the gallery and captioned as such.
- Alt text: written per photograph for the live listing; Portfolio images use '<title>, photograph n of N' (Instagram's own alt text is only 'Photo by ...').

## Videos

| Post | Date | Type | Attached to | Used on site |
|---|---|---|---|---|
| CZ4dEfeldVR | 2022-02-12 | reel | Meyersdal 5-bed (merged with CZ4aN__MjG5) | No (not in Portfolio) |
| CL4k5F1j7oP | 2021-03-01 | IGTV, 180 s | Eye of Africa feature | No (no stills) |
| CHnWCdspyhK | 2020-11-15 | reel, 14 s | 'Happy Sunday' brand post | No |
| CGUBEYbJmFz | 2020-10-14 | reel, 11 s | 'Brand New Listing Loading' teaser | No |

No video is used on the site; none belongs to a current listing.

## Rights

Photography was produced for the marketing agencies and republished by the account. The site credits the agency on every residence. Written permission for web reuse should be confirmed before launch.
