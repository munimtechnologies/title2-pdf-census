# Result: 1,067 US school district websites serve an unfinished accessibility statement template at one address (district-stock)

Status: graded. Pre-registered in [PREREG.md](PREREG.md) (committed 2026-11-08 before its crawl read any address) and run once, by sealed job `district-stock-v1` on 2026-11-08 (13:01 to 14:33 UTC), after the plan, `district_stock.py` 0.1.0 and the five files it pins were on main. **All four predictions held.**

Made by MV2 of Munim, Inc. with AI agents working for him; not yet checked by a person. Apache-2.0 (code), CC BY 4.0 (text and data). A placeholder says nothing about whether a website is accessible, the ADA Title II rule does not require an accessibility statement, and nothing here is legal advice. No district or vendor has been contacted about a page.

## Headline

**1,067 of the 11,581 US public school district website hosts (9.21%) serve an accessibility statement that still carries template placeholders at `/accessibility-statement`**, or 9.77% of the 10,920 hosts that answered.

Almost all of them are one 2017 statement template that MV2's [district-pages](../district-pages/DISTRICT-PAGES-RESULT.md) census found on sites with Finalsite markup (a school-website vendor). It begins "To help us make the Your School website a positive place for everyone, we've been using the Web Content Accessibility Guidelines (WCAG) 2.0" and gives accessibility@yourschool.com and 555-555-5555 as the contact.

That is about 8 times the 129 such pages the district-pages census found by following home-page links in its sample of 2,500 districts, and more than 4 times the 235 unfinished vendor templates found at two stock addresses on 5,243 US city, county and town websites ([stock-153](../stock-153/STOCK-153-RESULT.md), [stock-revize](../stock-revize/STOCK-REVIZE-RESULT.md)).

Larger districts serve one more often: 198 of 1,256 answering hosts of districts of 50,000 or more people (15.76%, 95% CI 13.85-17.88%), against 869 of 9,664 answering hosts of districts under 50,000 (8.99%, 95% CI 8.44-9.58%).

## Predictions

| | Prediction | Result | Held |
|---|---|---|---|
| K1 | At least 400 hosts serve a placeholder page at `/accessibility-statement` | 1,067 | yes |
| K2 | Of the census-sampled hosts that serve a placeholder page there, at least 15% are districts for which the census counted no placeholder page | 136 of 257 (52.92%, 95% CI 46.82-58.93%) | yes |
| K3 | Of the hosts where the census read a placeholder page at this address, at least 90% still serve one | 119 of 119 (100%, 95% CI 96.87-100%) | yes |
| K4 | At least 95% of placeholder pages carry Finalsite markup | 1,066 of 1,067 (99.91%, 95% CI 99.47-99.98%) | yes |

Gates: the frame is the district-pages frame rebuilt by the pinned `district_pages.py` from the NCES Common Core of Data 2024-25 directory and the Census Bureau's SAIPE 2024 file: 11,581 website hosts, 1,322 of them in districts of 50,000 or more people (1 district dropped as planned), inside F1's 11,000 to 11,700 and 1,250 to 1,400. All 2,500 census rows were read (G0), and 10,920 of 11,581 hosts (94.29%) answered, above G1's 80%.

The plan expected about 570 placeholder pages from linked pages alone (K1); the full frame gave nearly twice that.

Within the census sample alone, the one address finds 257 hosts serving a placeholder page, against the census's 129 found by following links; 136 of the 257 are districts the census did not count, because their home page could not be read, linked no accessibility page the census read, or linked a different page (K2).

## What else the run shows (described, not graded)

- 2,284 pages could be read at the address (539 in districts of 50,000 or more, 1,745 under 50,000), and 1,067 of them (46.72%) keep a placeholder. 7,792 hosts answered 404 (no page at the address).
- By census record, the 1,067 are: 810 of districts outside the census sample, 119 at the address the census had read, 61 where the census read a different accessibility page, 49 whose home page linked no page the census read and 28 whose home page the census could not read.
- Of the 123 census placeholder pages at this address, 4 did not answer, and all 119 that answered serve the same visible text as when the census read them (the same text hash).
- Placeholders kept: 811 pages keep all three kinds ("Your School", a yourschool.com-style address and 555-555-5555), 237 keep only "Your School", and 19 keep another combination.
- 1,061 of the 1,067 carry the 2017 template's first sentence. 1,624 readable pages carry that sentence: 563 districts filled the template in, and 1,061 (65.33%) did not.
- 934 of the 1,067 keep the template's credit to the 2017 Accessibility Statement Generator.
- The highest WCAG version named is 2.0 on 1,044 of the 1,067 (97.84%), 2.1 on 13, 2.2 on 6, and none on 4. The ADA Title II rule (28 CFR 35.200) adopts WCAG 2.1 Level AA; 57 of the 1,067 mention Title II.
- Finalsite's 2026 sample statement ("built with WCAG 2.1 AA guidelines in mind") is on 2 pages, and neither keeps a placeholder.
- 1,981 of the 2,284 readable pages carry Finalsite markup. The one placeholder page without it keeps only the dummy phone number.
- The 1,067 are in 41 states, most in Ohio (107), Texas (99), New Jersey (96), California (91), New York (74) and Pennsylvania (73).
- No server answered 429 or 503, so no address was asked twice.

## What this adds

Web searches on 2026-11-08 find single live school pages with this template, but no count of how many districts serve it; this is the first. It shows that the unfinished statement is a vendor-level pattern: one sample text, at one address, carried unfilled into about a thousand district websites, most of them naming only WCAG 2.0. A district can check its own statement, or a draft, with MV2's free [a11y-statement-check](https://github.com/munimtechnologies/a11y-statement-check), which applies these placeholder rules; since its v0.2.0 it is also a GitHub Action that fails a pull request while a statement draft still has a placeholder.

## Honest limits

- One address per host, read once: a template under another address, on a school's own host or in a PDF is not found, so 1,067 is a floor, and a district may fix its page at any time.
- A page served at an address is not necessarily linked from the site: this study does not say whether visitors reach it.
- Hosts, not districts: districts sharing one website host are counted once, and SAIPE populations are model-based estimates.
- The flags are the census's rules (`district_check.py`), unchanged. Every census placeholder page that answered was flagged again (K3), but no page here has been checked by a person.
- The frame is regular, open districts with a website in the CCD; charter-only agencies, individual schools' own hosts and private schools are not in it.

## Files

`hosts-50k.csv` (one row per host of a district of 50,000 or more: status, a hash of the page text and the flags; no page text), `result.json` and `result.txt` are the run's output, unchanged. The under-50,000 table (`hosts-under50k.csv`, 2,066,333 bytes) is over the publishing tool's limit of 2,000,000 bytes per file, so it is here in two parts, `hosts-under50k-part1.csv` (5,130 rows, 1,026,349 bytes) and `hosts-under50k-part2.csv` (5,129 rows, 1,040,214 bytes): the same rows, split once in LEAID order, which join back byte for byte to the job's file (header once). `test_district_stock_result.py` (repository root) re-grades every measure, gate and prediction from the three tables with the pinned `district_stock.py`, checks that the parts join back to the job's file size, and checks every figure in this note against `result.json`.
