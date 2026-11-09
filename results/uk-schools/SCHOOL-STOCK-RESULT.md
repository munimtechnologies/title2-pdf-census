# Result: 667 school websites in England serve an unfinished accessibility statement template at one address (school-stock)

Status: graded. Pre-registered in [PREREG.md](PREREG.md) (committed 2026-11-09 before any school website was read) and run once, by sealed job `school-stock-v1` on 2026-11-09 (10:15 to 14:18 UTC), after the plan, `school_stock.py` 0.1.0 and the pinned checker were on main. **Two of the four predictions held (J1, J4) and two failed (J2, J3).**

Made by MV2 of Munim, Inc. with AI agents working in his name; not yet checked by a person. Apache-2.0 (code), CC BY 4.0 (text and data). Schools in England are exempt from the UK accessibility regulations (SI 2018/952, regulation 4(1)(c)) except for content needed for essential online administrative functions, so nothing here calls a school's statement a breach. A placeholder says nothing about whether a website is accessible; it says the statement was never finished. Nothing here is legal advice. No school or vendor has been contacted about a page.

## Headline

**667 of the 23,802 school website hosts in England's register (2.80%) serve an accessibility statement that still carries template placeholders at `/accessibility-statement/`**, or 10.40% of the 6,412 statement pages that could be read there. Behind those 667 hosts are 672 establishments, and 530 of the hosts are listed under a primary school.

Nearly all of them come from two templates that end with the same sentence ("... values diversity and inclusion and is committed to providing an accessible online experience"):

- 281 of the 667 carry that sentence and the Juniper Websites credit. Juniper's template keeps a bracketed school name such as "[School Name]": 273 of the 667 keep a bracketed school name, and 272 of those 273 carry the Juniper credit.
- 333 carry that sentence without the Juniper credit, and 327 of those 333 keep exactly three fields of GOV.UK's sample statement and nothing else that the checker flags: "[email address]", "[phone number]" and "[number]" (the days a reply takes). One of these pages, opened once on 2026-11-09 after the result came in, credits "Website design by Greenhouse School Websites", another school-website company. That is one page, not a count: an addendum to the planned follow-up, registered before it reads anything, will count that credit on all of them ([CREDIT-FOLLOWUP-ADDENDUM.md](CREDIT-FOLLOWUP-ADDENDUM.md)).
- 11 carry the Juniper credit without the sentence, and 42 carry neither.

## Predictions

| | Prediction | Result | Held |
|---|---|---|---|
| J1 | At least 400 hosts serve a page with a 0.3.0 placeholder at `/accessibility-statement/` | 667 | yes |
| J2 | At least 80% of those pages carry the Juniper Websites credit | 292 of 667 (43.78%) | no |
| J3 | At least 40% of read pages carrying the Juniper template's closing sentence keep a 0.3.0 placeholder | 614 of 2,639 (23.27%) | no |
| J4 | At least 50% of read pages using GOV.UK's compliance sentence name WCAG 2.2 as the highest version | 2,854 of 2,950 (96.75%) | yes |

Gates: The frame is the 24,659 establishments (23,802 hosts) in the Department for Education's Get Information about Schools file of 2026-11-09 that list a website. All three frame parts matched their registered hashes and none was dropped (F1). 22,692 of 23,802 hosts (95.34%) answered, above G1's 80%, and the checker matched release v0.3.0 byte for byte (P0).

## Why J2 and J3 failed

J2 assumed the unfinished pages were nearly all one vendor's. They are not: about half come from the second template above, whose pages carry no Juniper credit. (The credit pattern also misses Juniper's older brands, e4education and PrimarySite, as the follow-up registered before this result explains: [CREDIT-FOLLOWUP-PREREG.md](CREDIT-FOLLOWUP-PREREG.md).) J3 assumed the closing sentence marked Juniper's template alone. It marks the second template too, and most pages carrying it were filled in: 2,025 of them keep no placeholder.

## What else the run shows (described, not graded)

- 6,412 hosts serve a readable statement page at the address. 13,806 hosts answered 404 (no page at the address), 1,351 disallowed the address in robots.txt, 1,110 did not answer at all, 411 redirected to a home page and 409 served a page that does not mention accessibility.
- The Juniper credit is on 4,852 of the 6,412 readable pages (75.67%), and 292 of those 4,852 (6.02%) keep a placeholder.
- Fields of Juniper's template that checker 0.3.0 does not know ("[Website Link and Date]", "[Accessibility Email Address]", "[School Phone Number]", the sample notice and its editing notes) are on 240 pages, 126 of which have no 0.3.0 placeholder, so 793 readable pages carry one or the other. 129 pages carry the long sample variant, and 50 name the vendor's build address instead of the school's.
- 30 of the 667 keep a placeholder of the 2017 US template that MV2's [district-stock](../district-stock/DISTRICT-STOCK-RESULT.md) census found on 1,067 US school-district hosts ("the Your School website", a yourschool.com-style address or 555-555-5555), and 20 of those 30 are independent schools. Read pages of independent schools keep a placeholder more often: 27 of 117 (23.08%), against 310 of 3,146 academies (9.85%) and 301 of 2,640 local-authority maintained schools (11.40%).
- 627 of the 667 name WCAG 2.2 as the highest version, 30 name 2.0, 9 name 2.1 and 1 names none.
- Most are in the South East (145) and the East of England (107).
- The 667 pages have 663 distinct texts, 10 were served from another host, and 17 hosts answered 429 or 503 and were asked once more after 30 seconds.

## What this adds

Web searches on 2026-11-09 found live English school pages with unfilled statement fields, and one 2026 review of 303 UK council statements that scores their sections, but no count of unfinished statements on UK school websites; this is the first. Fewer English school hosts serve a placeholder at this address than US school districts did (2.80% against 9.21% in district-stock), mostly because most English hosts have no page there at all, and among readable pages the share is 10.40% against 46.72%. As in the US, the unfinished statement is a vendor-level pattern: two template texts carried unfilled into hundreds of school websites. A school, trust or website company can check a statement or a draft with MV2's free [a11y-statement-check](https://github.com/munimtechnologies/a11y-statement-check), whose GOV.UK rules (since v0.3.0) flag the fields counted here. Juniper's own fields and editing notes are not yet among its rules.

## Honest limits

- One address per host, read once on one day: a statement under another address, on a trust's site or in a PDF is not seen, so 667 is a floor, and a school may fix its page at any time.
- A credit in the HTML shows who built or once built the site, not who wrote the statement. The second template's vendor rests on one page until the follow-up counts it.
- The GIAS website field is what schools report and can be out of date; hosts shared by several establishments are counted once.
- The flags are the pinned rules, unchanged; no page here has been checked by a person.

## Files

`hosts-part1.csv` to `hosts-part4.csv` (one row per host: establishment fields from GIAS, status, a hash of the page text and the flags; no page text and no person's name), `result.json` and `result.txt` are the run's output, unchanged. `test_school_stock_result.py` (repository root) re-grades every measure, gate, prediction and described count from the four tables with the pinned `school_stock.py`, checks each table's bytes against `result.json`, and checks every figure in this note.
