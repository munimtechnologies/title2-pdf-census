# council-agree: do two automated censuses of UK council accessibility statements score the same page? (pre-registration)

Registered 2026-11-10, before the comparison is run and before any page is read for this study.
Script: `council_agree.py` 0.1.0 with its offline tests (`test_council_agree.py`). Made by MV2 of
Munim, Inc. with AI agents; not yet checked by a person. Code Apache-2.0; this text and MV2's
data CC BY 4.0.

## Why

Two open, automated censuses now cover the accessibility statements of UK councils:

- Accessibility.build's "State of Accessibility Statements 2026"
  (https://accessibility.build/research/accessibility-statements-2026), measured on 2026-09-02,
  gave 303 UK local authorities to its statement checker. It found 206 statements and scored each
  against 8 mandatory elements; 123 had all of them and 23 were "missing most". Its council table
  is published under CC BY 4.0 (attribution: Accessibility.build, https://accessibility.build/research;
  sample from Wikidata), with the statement address, the number of elements found and how the
  address was found ("via"), but not which elements were missing.
- MV2's council-stock census ([COUNCIL-STOCK-RESULT.md](COUNCIL-STOCK-RESULT.md)), read on
  2026-11-10, found 284 statements on the 379 website hosts of the UK's 385 principal councils.
  Its reader follows a link from a page that only links to the statement (found_by `hub`).

Before registering this plan we looked at the header and the first five rows of Accessibility.build's
table and at nothing else in it. All five are scored 1 of 8. For four of them (Derby, City of
York, Elmbridge, Lichfield) MV2's table holds a statement at a different address, reached through
a hub page, that names a WCAG version; three of the four also give a date. Accessibility.build
says pages that look like hubs are "reported separately and not scored". This study tests whether
that pattern holds across the whole table: is a very low score usually a page in front of the
statement rather than the statement? We found no published comparison of two automated
accessibility statement censuses, council by council.

## Data (fixed now)

- Accessibility.build's table: fetched once, by the job, from
  `https://accessibility.build/api/research/accessibility-statements?table=councils&format=csv`
  (robots.txt honoured). Its SHA-256, size and fetch time are recorded. A copy goes into the
  results with attribution, minus any row naming the one word MV2's publishing tool refuses
  (counted). The table is used only if its header is
  `name,host,statementUrl,percent,verdict,mandatoryPassed,mandatoryTotal,via`, it has 150 to 400
  rows and every row is scored out of 8 (gate A1). The table may have changed since 2026-09-02;
  the result says which version was read.
- MV2's table: `hosts.csv` in this folder, unchanged since the census (99,491 bytes, 379 rows,
  SHA-256 d2f696ed2158...).

## Method

- Score groups by Accessibility.build's count of mandatory elements: low (0 to 3 of 8, fewer than
  half), partial (4 to 7), full (8 of 8).
- Matching: a row matches MV2's row with the same host (`www.` dropped); if none, the MV2 host that
  is the host, or the nearest parent of the host, of the scored address; if none, the one MV2 row
  whose statement address has that host. A second row on an MV2 host already matched is kept
  unmatched. "Both found" means the row matches an MV2 row whose status is `ok`.
- Same address: host without `www.` plus path, lower case, without a trailing slash, query or
  fragment.
- Re-read: for every both-found row whose address differs from MV2's, the address
  Accessibility.build scored is read once (crawl order by SHA-256 of the seed
  `council-agree-2026-11` plus the host; 4 councils at a time; robots.txt first; a 1-second pause
  after each request; a 429 or 503 is asked once more after 30 seconds). It is read with the same
  pinned code as November, `council_stock.py` 0.1.0 and `statement_template_check.py` 0.3.0, each
  checked against the SHA-256 in November's `result.json`. Stored: the answer, whether the page
  passes `council_stock.py`'s statement test, whether it links to MV2's statement address (same
  address rule), whether it now redirects there, its text length, highest WCAG version and date.
  No page text is stored.

## Gates (nothing is graded unless all hold)

- P0: this file is on main, and both pinned scripts match November's hashes.
- F1: MV2's `hosts.csv` matches the bytes above.
- A1: Accessibility.build's table has the registered form (above).
- G1 (at least 120 councils where both tables found a statement).

## Predictions (fixed before the comparison is run)

- H1 (at least 60% of the low-score rows where both found a statement give an address different
  from MV2's). Graded only with at least 10 rows.
- H2 (at least 80% of the full-score rows where both found a statement give MV2's address).
  Graded only with at least 60 rows.
- H3 (at least 60% of the re-read low-score pages that answer with HTML link to MV2's statement
  address). That is, they are pages in front of the statement. Graded only with at least 8 pages.
- H4 (at least 90% of the full-score rows at the same address carry a date MV2's reader took in
  November). Accessibility.build found a preparation or review date in every full-score statement;
  this checks MV2's date reader against it. Graded only with at least 50 rows.

The result is published whether the predictions hold or not.

## Described, not graded

How rows matched; score groups, verdicts, "via" values and scores; MV2's status for every matched
row (robots, not found, ok) and MV2 statements with no row in Accessibility.build's table; per
score group the same and different addresses, MV2 statements reached through a hub, MV2 dates and
WCAG 2.2; for re-read pages the answer, statement test, links and redirects.

## Limits

The two censuses read the pages two months apart, with different samples (Wikidata's 303 local
authorities against MV2's 385 principal councils) and different readers. A page may have changed
in between, so a re-read in November shows what that address serves now, not what was scored in
September. Accessibility.build publishes only how many elements it found, not which ones, so H4
checks dates only where it found every element. A link from the scored page to MV2's statement
shows the page sits in front of the statement; it does not prove which page Accessibility.build's
checker read. Neither census tests whether a website is accessible or whether a statement is
true, and nothing here calls a council in breach or faults either census's authors.
