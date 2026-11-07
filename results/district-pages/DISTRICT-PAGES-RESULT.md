# Result: what US school districts' accessibility pages promise (district-pages)

Status: graded. Pre-registered in [PREREG.md](PREREG.md) (committed 2026-11-06 before any school district's website was read) and run once, by sealed job `district-pages-v2` on 2026-11-06 (23:48 to 23:59 UTC), after the plan and the five pinned scripts were on main. Four of the six predictions held; D3 and D5 failed. (The first job, `district-pages-v1`, stopped before reading any district page because one of its test commands used a shell wildcard; v2 is the same code with exact file names.)

Made by MV2 of Munim, Inc. with AI agents working for him; not yet checked by a person. Apache-2.0 (code), CC BY 4.0 (text and data). A statement's wording says nothing about whether a website is accessible, and nothing here is legal advice. No district or vendor has been contacted.

## Headline

**129 of the 933 district accessibility pages read (13.83%) are still a statement template with its placeholders in**: 41 of 415 pages in the 50k+ band and 88 of 518 under 50,000. The pages say "To help us make the Your School website a positive place for everyone, we've been using the Web Content Accessibility Guidelines (WCAG) 2.0", give accessibility@yourschool.com and 555-555-5555 as the contact, and most credit the Accessibility Statement Generator (copies of the text found on the web say it was "generated on 16th May 2017"). The study predicted at least 0.5% (D4); it found more than 25 times that.

The template pages share one platform: all 129 are on sites whose home page carries Finalsite markup (a school-website vendor), and they are 129 of the 451 accessibility pages read on Finalsite sites (28.60%). Web searches made after grading found the same text on many individual school sites with a "Powered by Finalsite" footer, one of them titled "TEMPLATE: New Client Site (Custom)", but no count of how many districts serve it.

In all, 2,245 home pages and 933 accessibility pages were read, 415 of them in the 50k+ band and 518 under 50,000, from a frame of 11,582 website hosts (1,322 of 50,000 or more) built from the NCES Common Core of Data 2024-25 and the Census Bureau's SAIPE 2024 school-district populations.

## Predictions

| | Prediction | Result | Held |
|---|---|---|---|
| D1 | Under 50,000: fewer than 55.71% of versioned pages name only WCAG 2.0 | 185 of 417 (44.36%, 95% CI 39.67-49.16%) | yes |
| D2 | Under 50,000: fewer than 10% of pages carry the stock sentence | 1 of 518 (0.19%, 95% CI 0.03-1.09%) | yes |
| D3 | The share of versioned pages naming WCAG 2.1 or 2.2 is at least 5 points higher at 50k+ than under 50,000 | 136 of 277 (49.10%, 95% CI 43.26-54.96%) against 232 of 417 (55.64%, 95% CI 50.84-60.33%) | no |
| D4 | At least 0.5% of all pages read carry a placeholder | 129 of 933 (13.83%, 95% CI 11.76-16.19%) | yes |
| D5 | Under 50,000: at least 68.2% of home pages read link to an accessibility, Section 508 or ADA page | 528 of 1,564 (33.76%, 95% CI 31.46-36.14%) | no |
| D6 | Under 50,000: at least 22.15% of pages name Title II | 233 of 518 (44.98%, 95% CI 40.75-49.29%) | yes |

- **D3 failed the other way:** at 50k+ the share naming 2.1 or 2.2 is 6.54 points lower than under 50,000, not 5 points higher.
- **D5 failed by half:** only a third of smaller districts' home pages link to such a page under the census's link rules, against 68.2% for cities and counties of 50,000 or more. The rules read the home page's HTML as served; menus that a page builds with JavaScript are not seen, so this may undercount links on some school platforms.
- **D6 held by double:** smaller districts' pages name Title II about twice as often as large cities' pages did.

## Found after grading (not pre-registered)

These counts were made after the predictions were graded, to understand D4. They are reproducible from `rows.csv` and checked by the test, but they were not predicted.

- Of the 129 template pages, 91 keep all three, 35 keep only "the Your School website", 2 keep only the address and the phone number, and 1 keeps the name and the address.
- The template's version sentence is far more common than its placeholders: 245 of 933 (26.26%) carry the template's first sentence in the saved snippet (100 of 415 in the 50k+ band and 145 of 518 under 50,000), including 126 of the 129 template pages. 157 pages credit the Accessibility Statement Generator, 106 of them among the 129.
- The template drives much of D1. Leaving out the template pages, 99 of 330 (30.00%) name only WCAG 2.0 of the remaining versioned pages under 50,000.
- AudioEye's script is on 297 of 681 (43.61%) home pages read in the 50k+ band and 250 of 1,564 (15.98%) under 50,000.

## Described (pre-registered, not graded)

- Dates: 3 under-50,000 pages give April 26, 2028; 4 pages of 50k+ districts still give April 24, 2026 and 1 gives April 26, 2027.
- No page read gives the 50,000 threshold in students (the error in one vendor's guidance that the plan looked for), and no page carries that vendor's newer template line.
- Section 504 on 202 of 415 pages in the 50k+ band and 288 of 518 under 50,000; Title II on 140 of 415 at 50k+.
- The full description by band (platforms and overlays on home pages, vendors named, generator credits, contact details) is in `result.txt`.

## Honest limits

- One page per district, read once; a statement elsewhere on the site, in a PDF or on another host is not found. 76 home pages and 41 accessibility pages answered "too many requests" (HTTP 429).
- The template is counted by its placeholders; partly edited copies (for example with a district's name filled in) are counted only in the after-grading sentence count.
- SAIPE populations are model-based estimates; districts sharing one host are counted once; the two bands are sampled at different rates, so pooled shares (D4) are not national estimates.
- `frame.csv` is not published: one district's name in the frame contains a word that MV2's publishing tool blocks. That district is not in the sample. The frame can be rebuilt from the two federal files with `python district_pages.py --dry-run --out-dir <folder>`.

## Files

`rows.csv` (one row per sampled district: statuses, a hash of the page text, the flags and short snippets around a WCAG version, a date or the threshold, with email addresses and phone numbers removed), `sample.csv`, `result.json` and `result.txt` are the run's output, unchanged. `test_district_pages_result.py` (repository root) re-grades every measure and prediction from `rows.csv` with the pinned `district_pages.py` and checks every figure in this note.
