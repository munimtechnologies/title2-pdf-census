# Pre-registration: what US school districts' accessibility pages promise (district-pages)

Status: plan, committed on 2026-11-06 before any school district's website was read. The crawl
starts only once this file, `district_pages.py` 0.1.0 and `district_check.py` 0.1.0 are on main,
and it runs main's copies of the five scripts it uses.

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Apache-2.0 (code),
CC BY 4.0 (text and data). A statement's wording is not a judgment of whether a website is
accessible, and nothing here is legal advice.

## Why

Public school districts are Title II entities. Under 28 CFR 35.200 (2024) their web content
must meet WCAG 2.1 Level AA, by April 26, 2027 if the district's total population is 50,000 or
more and by April 26, 2028 if it is smaller (the dates as moved by the Justice Department's
interim final rule of April 20, 2026). The rule counts the population of the district's area,
not its enrollment.

MV2's two earlier censuses read the accessibility pages of US cities, counties and towns:
[results/a11y-pages](../a11y-pages/) (50,000 or more people) and
[results/small-pages](../small-pages/SMALL-PAGES-RESULT.md) (10,000 to 49,999). Most of those
pages promise only WCAG 2.0, and most small-government pages carry one vendor's stock sentence.
Searches through 2026-11-06 found vendor guides and automated scans of school websites, but no
count of what school districts' accessibility statements actually say. School websites mostly
run on other platforms (Finalsite, Apptegy, Edlio, SchoolMessenger Presence and others), and
some vendors publish statement templates with placeholders: Finalsite's support article
"2026 ADA WCAG 2.1 Accessibility at Finalsite" offers one with "[Your School]", "built with
WCAG 2.1 AA guidelines in mind" and "within # business days", and the same article gives the
threshold once as "districts with 50,000+ students".

## Frame and sample (fixed now)

- **Districts:** the NCES Common Core of Data LEA directory 2024-25
  (`ccd_lea_029_2425_w_1a_073025.zip`): regular districts (`LEA_TYPE` 1 or 2) that are open
  (`SY_STATUS` 1, 3, 4, 5 or 8) and list a website.
- **Population:** the Census Bureau's SAIPE 2024 school-district file (`ussd24.txt`; SAIPE 2023
  if 2024 cannot be read), total population, matched on the 7-digit LEAID. Districts without a
  SAIPE row are left out. Band: **50k+** (50,000 or more) or **under50k**.
- **One row per website host** (the `www.` dropped): the district with the largest population
  is kept, then the lowest LEAID.
- **Sample:** in the order of SHA-256(`district-pages-2026-11` + LEAID), the first **800**
  districts of 50k+ and the first **1,700** of under50k (all of a band if it has fewer).
- **Gate F1:** the frame has 8,000 to 16,000 districts and 400 to 2,500 of them are 50k+.
  Otherwise nothing is read.

**Dry run (2026-11-06, job district-dry-v1; reads no district page):** all 18 offline tests
passed; 19,630 CCD rows and 13,131 SAIPE rows were read; the frame holds 11,582 website hosts,
1,322 of them 50k+ and 10,260 under50k, so F1 holds; the sample is 800 + 1,700 = 2,500. The
crawl rebuilds the frame and sample from the same two files with the same code.

## Reading (fixed now)

The census's requests and link rules, unchanged (`a11y_pages.py`): robots.txt honoured, the
home page, then up to three same-site links ranked accessibility path, accessibility text,
Section 508, ADA; the first that returns readable HTML of 200 or more characters is the
district's accessibility page. Each page is read by `district_check.check_text`:
`statement_check.py`'s version, stock-sentence, date and contact rules and
`template_check.py`'s four placeholder flags, both unchanged, plus five school placeholder
flags (a bracketed "[Your School]", "[School Name]", "[District Name]" or "[Insert ...]";
"the Your School website"; a "yourschool.com"-style address; 555-555-5555; "within #
business days"), the 50,000 threshold given in students or enrollment, the Office for Civil
Rights, Section 504, a school-website vendor named on the page, the Finalsite template line and
a statement-generator credit. Home pages are also checked for platform markup and overlays.

**Gate G1:** at least 1,000 home pages and 400 accessibility pages read across both bands.

## Predictions (graded by `district_pages.grade`)

| | Prediction | Graded only if |
|---|---|---|
| **D1** | Under50k: fewer than **55.71%** of pages that name a WCAG version name only WCAG 2.0 (the 50,000+ cities' share) | 150 versioned pages |
| **D2** | Under50k: fewer than **10%** of pages carry the stock sentence "We work to comply with Section 508 as well as" | 300 pages |
| **D3** | The share of versioned pages whose highest version is 2.1 or 2.2 is at least **5 points** higher in 50k+ than in under50k | 80 versioned pages in each band |
| **D4** | At least **0.5%** of all pages read carry a placeholder (any of the nine flags) | 400 pages |
| **D5** | Under50k: at least **68.2%** of home pages read link to an accessibility, Section 508 or ADA page (the 50,000+ cities' share) | 600 home pages |
| **D6** | Under50k: at least **22.15%** of pages name Title II (the 50,000+ cities' share) | 300 pages |

Reasons, written before reading: school platforms advertise WCAG 2.1 AA, so fewer pages should
stop at 2.0 (D1) and few should carry the city vendor's sentence (D2); larger districts update
more (D3); vendor templates with placeholders exist (D4); school-website footers commonly link
an accessibility page (D5); districts have been told about Title II by their vendors and state
agencies since 2024 (D6).

**Described, not graded:** everything by band: versions, Section 508, 504, OCR, contact,
each date, the students threshold, the Finalsite line, generator credits, vendors named,
platform markup and overlays on home pages, and home pages with no same-site link but an
off-site one.

## Honest limits

- One page per district; a statement elsewhere on the site, in a PDF or on another host is not
  found. A page built by JavaScript can read as short.
- SAIPE populations are model-based estimates; the rule's own count may differ near 50,000.
- Districts sharing one host are counted once.
- The two bands are sampled at different rates, so pooled shares (D4 only) are not national
  estimates.
- A district whose name contains a word that MV2's publishing tool blocks will have its name
  and links withheld as `[withheld]` in the published tables; its LEAID is kept. The dry run
  shows one such district in the frame and none in the sample.

## After grading

`rows.csv`, `frame.csv`, `sample.csv`, `result.json` and `result.txt` go to
`results/district-pages/` with a result note and a test that re-grades every figure from the
saved table. Results are published whether the predictions hold or not.
