# council-agree: do two automated censuses of UK council accessibility statements score the same page? (result)

Graded 2026-11-11 from sealed job council-agree-v1, which ran on 2026-11-10; the 22 re-read pages
were requested within 30 seconds (21:31:23 to 21:31:53 UTC on 2026-11-10). Plan: [AGREE-PREREG.md](AGREE-PREREG.md),
registered before the comparison was run. Script: `council_agree.py` 0.1.0, with the pinned
`council_stock.py` 0.1.0 and `statement_template_check.py` 0.3.0. Data:
[agree/](agree/). Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Code
Apache-2.0; this text and MV2's data CC BY 4.0. Accessibility.build's table is theirs, copied
unchanged under CC BY 4.0 (Accessibility.build, https://accessibility.build/research; sample from
Wikidata).

**All four predictions held (H1, H2, H3, H4).**

**12 of the 23 councils whose pages Accessibility.build scored lowest (52.17%) have that page
link straight to the statement MV2's reader found.** Where both censuses read the same page, they
agree closely: the full-score rows almost always give the address MV2's reader found, and that
statement carries a date MV2's reader could take.

## What was compared

- Accessibility.build's "State of Accessibility Statements 2026" council table
  (https://accessibility.build/research/accessibility-statements-2026, measured 2026-09-02),
  fetched at 21:31:23 UTC (206 rows, 26,695 bytes, SHA-256 `4beb4c416e85`) on 2026-11-10. Of its 206
  rows, 23 rows score 0 to 3 of 8 ("not-compliant"), 60 score 4 to 7 ("missing-information") and
  123 score 8 of 8 ("compliant").
- MV2's council-stock table ([hosts.csv](hosts.csv), read 2026-11-10, unchanged; see
  [COUNCIL-STOCK-RESULT.md](COUNCIL-STOCK-RESULT.md)).

204 rows matched an MV2 host (201 by host, 3 by the scored address's host) and 2 did not. Both
censuses found a statement for 189 councils, above G1's 120. For the other 15 matched rows MV2's
November reader found no statement (14) or was refused by robots.txt (1). MV2's census found 95
statements on hosts that have no row in Accessibility.build's table (its sample is Wikidata's 303
local authorities, MV2's is the 385 principal councils). 196 of Accessibility.build's 206 rows
were found through a footer link and 10 at a common path.

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| H1: low-score rows (both found) at an address different from MV2's | at least 60% | 13 of 17 (76.47%) | yes |
| H2: full-score rows (both found) at MV2's address | at least 80% | 110 of 115 (95.65%) | yes |
| H3: re-read low-score pages that link to MV2's statement | at least 60% | 12 of 13 (92.31%) | yes |
| H4: full-score rows at the same address that MV2's reader dated | at least 90% | 107 of 110 (97.27%) | yes |

## The lowest scores

Accessibility.build scored 23 councils' pages 0 to 3 of its 8 mandatory elements. MV2's reader also
found a statement for 17 of the 23; for the other 6, MV2's November reader found no statement
either. 13 of the 17 give an address different from MV2's. All 13 of those addresses answered with
HTML when read again; none passed the statement test of MV2's reader, and 12 link straight to the
statement MV2's reader found. The one exception (shetland.gov.uk) neither passed the statement test
nor linked to MV2's statement address.

Read in November, all 12 of those statements name a WCAG version (10 name 2.2, 2 name 2.1) and 11
give a date; 2 of the dates are later than 2 September 2026, so those two statements may have been
written or updated after Accessibility.build's measurement. On the 4 low-score rows at the same
address, MV2's reader took a WCAG version from 1 and a date from 2.

Accessibility.build says pages that read like an accessibility hub rather than a statement are
"reported separately and not scored". These 12 pages were scored. A reader that follows one more
link from such a page would likely score most of these councils differently. That is a
suggestion from this comparison, not something it tested.

## The full and partial scores

110 of the 115 full-score rows where both found a statement give MV2's address, and 107 of those
110 carry a date MV2's reader took (H4). 5 full-score rows give another address; 4 of those pages
answered with HTML when read again and all 4 pass the statement test (the fifth answered 404). 53
of the 57 partial-score rows where both found a statement give the same address. Of the 22
addresses read again, 2 answered 404 in November.

Found after the run and not pre-registered: 37 of the 112 full-score statements that MV2's reader
dated (33.04%) carry a date before 1 November 2025, and 85 of the 115 (73.91%) name WCAG 2.2. A
statement can have every mandatory element and still carry a review date more than a year old;
GOV.UK's sample statement asks for a review at least once a year.

## Limits

The two censuses read the pages two months apart, with different samples and different readers. A
page may have changed in between, so a November re-read shows what an address serves now, not
what was scored in September. Accessibility.build publishes how many elements it found, not which
ones. A link from a scored page to MV2's statement shows the page sits in front of the statement;
it does not prove which page Accessibility.build's checker read. Neither census tests whether a
website is accessible or whether a statement is true. Nothing here calls a council in breach or
faults either census's authors: their open, CC BY table is what made this comparison possible.

## Files

- `agree/agree.csv`: one row per Accessibility.build row, joined to MV2's row, with the re-read
  answer (addresses, counts, a WCAG version and a date; no page text).
- `agree/accessibility-build-councils.csv`: Accessibility.build's table as fetched (CC BY 4.0).
- `agree/result.json`, `agree/result.txt`: the job's output, unchanged.
- `test_council_agree_result.py` (repository root): rebuilds the join from the two tables,
  re-grades every measure, prediction and described count with the pinned `council_agree.py`, and
  checks every figure in this note.
