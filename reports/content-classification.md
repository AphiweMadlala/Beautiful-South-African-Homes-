# Content Classification

All 380 posts on @beautifulsouthafricanhomes (11 Oct 2019 to 27 Aug 2026), classified by `scripts/build_data.py`.
Machine-readable: `data/post-classification.json` (category, tags, reason, propertyKey per post).

## Totals

| Category | Posts | Notes |
|---|---|---|
| FOR SALE | 1 | Verified live on the marketing agency's site (24 Sep 2026). |
| UNDER OFFER | 0 | No post states this status. The only 'sold' strings are hashtags (#sold) and a commenter's emoji. |
| SOLD | 0 | No post states this status. The only 'sold' strings are hashtags (#sold) and a commenter's emoji. |
| WITHDRAWN | 0 | No post states this status. The only 'sold' strings are hashtags (#sold) and a commenter's emoji. |
| RENTAL | 2 | Excluded from all inventory. |
| PROPERTY TOUR | 0 | Secondary tag on 2 posts.  |
| FEATURED HOME | 365 | Sale features whose current availability is not verified. Become Portfolio candidates. |
| ARCHITECTURE | 0 | Secondary tag on 2 posts.  |
| DEVELOPMENT | 0 | No new-development or off-plan posts found. |
| AGENT COLLABORATION | 0 | Secondary tag on 240 posts.  |
| BRAND CONTENT | 9 | Quotes, teasers, #BlackoutTuesday, 'Brand New Listing Loading' reel. |
| EDITORIAL | 3 | Compilation posts reusing images from other features (kitchens, entertaining). |
| OTHER | 0 |  |

## By year

| Year | BRAND CONTENT | EDITORIAL | FEATURED HOME | FOR SALE | RENTAL |
|---|---|---|---|---|---|
| 2019 | 0 | 0 | 1 | 0 | 0 |
| 2020 | 8 | 3 | 158 | 0 | 0 |
| 2021 | 1 | 0 | 126 | 0 | 0 |
| 2022 | 0 | 0 | 67 | 0 | 1 |
| 2023 | 0 | 0 | 10 | 0 | 1 |
| 2024 | 0 | 0 | 3 | 0 | 0 |
| 2026 | 0 | 0 | 0 | 1 | 0 |

## Excluded posts

| Date | Post | Category | Reason |
|---|---|---|---|
| 2023-05-01 | [CrtX0X9tq97](https://www.instagram.com/p/CrtX0X9tq97/) | RENTAL | caption offers the home for rent (price per month) |
| 2022-10-25 | [CkJJNPaDX6O](https://www.instagram.com/p/CkJJNPaDX6O/) | RENTAL | caption offers the home for rent (price per month) |
| 2021-01-23 | [CKYvTW9j4W4](https://www.instagram.com/p/CKYvTW9j4W4/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |
| 2020-11-21 | [CH3EBygJlL2](https://www.instagram.com/p/CH3EBygJlL2/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |
| 2020-11-15 | [CHnWCdspyhK](https://www.instagram.com/p/CHnWCdspyhK/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |
| 2020-10-14 | [CGUBEYbJmFz](https://www.instagram.com/p/CGUBEYbJmFz/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |
| 2020-08-23 | [CEPdh9WpuTE](https://www.instagram.com/p/CEPdh9WpuTE/) | EDITORIAL | multi-property compilation reusing images from other features |
| 2020-07-25 | [CDE1PKoJFlY](https://www.instagram.com/p/CDE1PKoJFlY/) | EDITORIAL | multi-property compilation reusing images from other features |
| 2020-07-17 | [CCwS-MnJTy9](https://www.instagram.com/p/CCwS-MnJTy9/) | EDITORIAL | multi-property compilation reusing images from other features |
| 2020-06-02 | [CA72WJCphyu](https://www.instagram.com/p/CA72WJCphyu/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |
| 2020-05-24 | [CAlMK7lJIj4](https://www.instagram.com/p/CAlMK7lJIj4/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |
| 2020-04-29 | [B_ked9XFUQ0](https://www.instagram.com/p/B_ked9XFUQ0/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |
| 2020-04-29 | [B_j3U0klNiN](https://www.instagram.com/p/B_j3U0klNiN/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |
| 2020-04-29 | [B_i2YkFlMWr](https://www.instagram.com/p/B_i2YkFlMWr/) | BRAND CONTENT | no listing data; motivational / teaser / cause post |

## Method

- Rentals: caption offers the home for rent, or prices are per month (`p/m`). One false positive (an agency named 'Eagle Canyon Property Sales & Rental') was excluded by requiring an explicit rental offer.
- AGENT COLLABORATION tag: caption names an agency (not 'DM US').
- ARCHITECTURE tag: caption names an architect rather than 'DM for credits' (2 posts).
- PROPERTY TOUR tag: reel/IGTV video of a property (2 posts attached to properties).
- Status words: no caption declares SOLD, UNDER OFFER or WITHDRAWN, so nothing is classified that way from Instagram alone.
