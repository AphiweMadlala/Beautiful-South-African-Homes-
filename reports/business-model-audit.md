# Business Model Audit: Beautiful South African Homes

Checked: 24 September 2026. Sources: full Instagram feed (380 posts, Apify), profile data, related profiles, agency pages. Raw captures in `data/raw/`.

## Conclusion

**F. Combination: C (property marketing platform) + D (media / curation platform) + E (lead generation).**
It is **not verified** as an estate agency (A) or as an agent/team (B) in its own name. There is, however, strong **inferred** evidence that the account is operated by, or closely tied to, two practising estate agents (see "Operator link" below). That must be confirmed with the client before the site says anything about mandates either way.

## VERIFIED

| Fact | Evidence |
|---|---|
| Instagram business account, category "Real Estate", 28,612 followers, 1,145 following, 380 posts | `data/raw/profile.json` |
| Bio: "Proudly South African / Showcasing SA's most beautiful homes & destinations / Luxury rentals & sales / Business : beautifulsahomes@gmail.com" | profile |
| No external website link | profile (`externalUrl: null`) |
| Listings are credited to external agencies on the caption template `Contact 📲 / Details / Agency🏛 / Architects` | 244 posts carry `Agency🏛`; 55 distinct agencies named |
| The account invited agents to feature listings: "To feature your listings on our platform get in contact with us and we will gladly assist you" | 130 posts, first 26 May 2021, last 5 Jul 2023 |
| The account is dormant relative to its history: 169 posts in 2020, 127 in 2021, 68 in 2022, 11 in 2023, 3 in 2024, 0 in 2025, 1 in 2026 | `data/instagram-posts.json` |
| Latest post (27 Aug 2026) is a collaboration with @12digitalmedia, tagging @12lve_propertygroup; the listing is live on 12LVE's site at R 9 000 000 | `data/verification.json` |
| Two rental offers were published (2023 Camps Bay R300 000 p/m; 2022 Meyersdal) | classification |
| No post claims a sole or exclusive mandate in the account's own name | full-caption search |
| @exotic_global_homes ("A property blog featuring some of the finest homes from around the Globe", "DM Us To Feature Your Home or Listings", ⚜️) is tagged on 234 BSAH posts and co-authored 8 | `data/raw/related-profiles.json`, posts |
| @real_estate_bros is "Shaun & Gabriel, Real Estate", bio "@12lve_propertygroup, Real Estate Brokers, Buying, Selling, Rentals", ⚜️, website 12lve.co.za | `data/raw/related-profiles.json` |

## INFERRED (strong, not proven)

1. **Operator link.** @real_estate_bros, @exotic_global_homes and BSAH share the ⚜️ device, the caption voice and the "feature your listings" offer. @real_estate_bros is co-author on BSAH posts and credited as contact ("@real_estate_bros & ...") on several Allegiance Properties Soma features. A "Shaun Masilo" is credited as an agent in 2021; Gabriel Masilo is principal of 12LVE Property Group and co-founder of 12 Digital Media (the Aug 2026 collaborator). **Inference:** BSAH is likely run by, or closely associated with, Shaun and Gabriel Masilo.
2. **Consequence.** The one verified for-sale listing is marketed by the agency of the likely operators. That is legitimate, but it means the platform is not purely independent media. The site must not state "Beautiful South African Homes does not hold sales mandates" as an absolute until confirmed. The current site copy has been neutralised to "each residence is marketed by the agency credited on its page".
3. **Revenue model.** Features may be paid or reciprocal (agents gain exposure; platform gains content). No pricing or "paid partnership" flags exist (`paidPartnership` false on all posts).
4. **Johannesburg South origin.** Allegiance Properties Soma (Meyersdal / Eye of Africa) is the second most credited agency (28 homes), consistent with the operators' earlier affiliation.

## UNKNOWN

- Legal entity, registration, PPRA (FFC) status of the platform itself.
- Whether features are paid, and at what price.
- Whether the business still actively accepts submissions (last invitation July 2023; one feature since).
- Whether "Luxury rentals" in the bio is a current service.
- Current relationship with @exotic_global_homes (581 followers, last post Apr 2023).

## What the site does with this

- Sales-first. Rentals excluded. "For Sale" shows verified listings only.
- Every residence carries **Marketed by** (agency, and agent where verified) and **Featured by** Beautiful South African Homes.
- "Feature a Property" is offered because the invitation is verified historically; copy promises review, not publication, and no backend is implied.
- No claims about mandates in either direction, pending client confirmation.
