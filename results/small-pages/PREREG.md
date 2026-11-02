# What do the accessibility pages of smaller US local governments promise? (pre-registration)

Written 2026-11-02, before any page of this cohort was read. The crawl runs with the code next to
this file (`small_pages.py`, which uses `a11y_pages.py` and `statement_check.py` unchanged), and
only after this file and those three scripts are on the repository's main branch.

By AI agents working for MV2 of Munim, Inc.; not yet checked by a person. Text CC BY 4.0, code
Apache-2.0.

## The question

The 2024 ADA Title II rule (28 CFR 35.200) adopts WCAG 2.1 Level AA for the websites of state and
local governments. The Justice Department's interim final rule of April 20, 2026 moved the
compliance dates by a year: April 24, 2026 became April 26, 2027 for governments of 50,000 or more,
and **April 26, 2027 became April 26, 2028 for governments of under 50,000 and special districts**.

The census in [results/a11y-pages](../a11y-pages/A11Y-PAGES-RESULT.md) read the accessibility
pages linked from the home pages of US cities and counties of 50,000 or more (808 pages read). It
found that 283 of the 508 pages naming a WCAG version (55.71%) name WCAG 2.0 as their highest, and
that 280 of the 808 carry one stock sentence ("We work to comply with Section 508 as well as WCAG
2.0 A and AA ..."). This test asks the same questions of smaller governments, which outnumber the
large ones several times over and have the later date, and adds one question only they raise: do
their pages still give April 26, 2027, the date that was theirs until April 2026?

## Why this is new

As far as we could find (searches on 2026-11-02), published 2026 work on government accessibility
(AccessLumens, Accessible Compliance Group's 15,481-site scan, WPPersona, UAIS) runs automated
scans of pages; none reads what accessibility statements promise, and none looks at governments of
under 50,000 by what their statements say about the moved dates.

## Cohort (fixed by the code before any page is read)

1. Wikidata, queried when the job runs: US cities, counties, consolidated city-counties and towns
   (the census's four types and their direct subclasses) with an official website, keeping
   population statements of 10,000 or more and dropping any item whose largest population is
   50,000 or more (the query is `COHORT_QUERY` in `small_pages.py`). One row per website host,
   largest population kept, as census.py 0.2.3 does.
2. Every government and every website host in the 50,000+ cohort (`results/v0.2.2/cohort.csv` at
   commit 279e85e) is left out.
3. If between 1,500 and 9,000 rows remain (gate C1), the first 2,500 in the order of
   SHA-256("small-pages-2026-11-02" + Wikidata id) are read. Otherwise nothing is graded.

Wikidata's populations are not the Census figures the rule uses, and some are old; a few places
near either edge may be on the wrong side of a line. This is a limit of the test, stated now.

## Method

The same requests as `a11y_pages.crawl_site`: robots.txt (honoured), the home page, then up to
three same-site links ranked by the census's link rules, keeping the first page that answers with
at least 200 characters of text. One site at a time per worker with a 1-second pause, under a
User-Agent that names Munim, Inc. and an email. Each page is read with `a11y_pages.classify` (WCAG
versions, Section 508, Title II, April 24, 2026, April 26, 2027) and with
`statement_check.check_text(small=True)` (the stock sentence, April 26, 2028, and its findings).

## Predictions

The first four compare this cohort with the 50,000+ census's figures, as fixed thresholds (point
estimates, not significance tests; 95% Wilson intervals are reported).

- **S1** (WCAG 2.0): of pages naming a WCAG version, the share whose highest is 2.0 is at least
  **55.71%**. Why: within the 50,000+ cohort, governments under 250,000 named a version more often
  than larger ones (67.1% against 45.2%), and the stock sentence that names 2.0 appears to come
  from a web platform's default page (the five checked were CivicPlus CivicEngage sites), which we
  expect smaller governments to edit less often. Graded if at least 200 pages name a version.
- **S2** (stock sentence): of pages read, the share carrying the stock sentence is at least
  **34.65%** (280 of 808 in the 50,000+ census). Graded if at least 400 pages are read.
- **S3** (Title II): of pages read, the share naming Title II is at most **22.15%** (179 of 808).
  Why: their date is further away. Graded if at least 400 pages are read.
- **S4** (a link at all): of home pages read, the share with at least one same-site link the rules
  pick as an accessibility page is below **68.2%** (815 of 1,195 in the 50,000+ census, by the same
  rules). Graded if at least 1,000 home pages are read.
- **S5** (the date that moved): of pages giving any of April 24, 2026, April 26, 2027 or April 26,
  2028, the share giving April 26, 2027 without April 26, 2028 is at least **40%**. Why: April 26,
  2027 was these governments' date for two years. Graded if at least 15 pages give a date (only 17
  of 808 did in the 50,000+ census, so S5 may well go ungraded).

A prediction below its minimum is reported as not graded, never as held or failed. Every gate,
threshold and the sample seed are constants in `small_pages.py`; changing any after the crawl voids
the test.

## Gates

- **P0**: this file is on main and main's `small_pages.py`, `a11y_pages.py` and
  `statement_check.py` are byte for byte the job's copies (line endings aside). Checked by the script
  before anything is read; it gives up after about an hour.
- **C1**: 1,500 to 9,000 eligible governments after the exclusions.

## Reported, not graded

Home-page and page outcomes, which link rank was used, WCAG version combinations, statement_check
findings, overlay scripts on home pages, Section 508, an email or phone number on the page, each
date's count (and pages giving only April 24, 2026, a date that never applied to these
governments), and the main counts by kind (city, county, town).

## What will be published

`result.txt`, `result.json`, the sampled cohort and a per-site table without page text (snippets
around a WCAG version or a date, with email addresses and phone numbers removed, stay in the job's
output and are published only if they name no person). Failed predictions are published as plainly
as held ones. Nothing here says any government is out of compliance: a statement's wording is not a
WCAG conformance judgment, and the Title II rule does not require a statement.
