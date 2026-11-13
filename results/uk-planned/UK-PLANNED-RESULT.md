# uk-planned result: planned review dates do not change the two UK censuses' shares; one "Next" link fooled the planned-date rule

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Code Apache-2.0; this text
and the tables CC BY 4.0. The plan, [PREREG.md](PREREG.md), was committed on 2026-11-11, before any
statement address was read again for this study.

## Headline

Sealed job uk-planned-v1 read the 479 statement addresses again; the 479 addresses were read from
18:27:20 to 18:31:34 UTC on 2026-11-13. **All four predictions held (Q1, Q2, Q3, Q4); Q4 held at
its limit.**

- 6 of the 470 statements read again (1.28%) give a planned date that the census date reader of
  `council_stock.py` 0.1.0 took as their latest review.
- 1 of the 446 dated statements (0.22%) goes from current to undated when planned dates are left
  out, and that one is an error of the planned-date rule, not a planned date: on
  https://www.westminster.gov.uk/accessibility a "Next" navigation link sits right before "Last
  updated: 1 October 2026", and the rule (copied from a11y-statement-check 0.7.0) reads "Next" as
  "the next review".
- The share of dated statements dated before 1 November 2025 moves by 0.15 points for councils (101
  of 265, 38.11%, to 101 of 264, 38.26%) and by 0.00 points for organisations (77 of 181, 42.54%).
  Leaving the Westminster error aside, no statement changes side of that line, so the published
  shares of [council-stock](../uk-councils/COUNCIL-STOCK-RESULT.md) and
  [govuk-stock](../govuk-orgs/GOVUK-STOCK-RESULT.md) stand as far as planned dates go.

## Frame and gates

The 486 rows with status ok (284 in the councils' table, 202 in the organisations' table) give 479
distinct addresses; no address is in both tables, and no address was withheld. F1 held.

P0 held: the job ran main's `planned_dates.py` 0.1.0 with `council_stock.py` 0.1.0 and
`statement_template_check.py` 0.3.0, and release v0.7.0 of a11y-statement-check still had the
planned-date rule byte for byte.

G1 held: 470 of the 479 addresses (98.12%) were read again as a statement; 8 did not answer and 1
(wirral.gov.uk) no longer reads as a statement.

## Predictions

| | Prediction | Measured | Held |
|---|---|---|---|
| Q1 | At most 5% of statements read again have a planned date the old reader took | 6 of 470 (1.28%) | yes |
| Q2 | At most 1% of dated statements go from current to dated before 2025-11-01 or undated | 1 of 446 (0.22%) | yes |
| Q3 | In each census the share dated before 2025-11-01 changes by at most 1.5 points | councils 0.15 points, organisations 0.00 points | yes |
| Q4 | At most 1 kept snippet, read by eye, is not about a planned review, update or publication | 1 of 7 (westminster.gov.uk) | yes |

Q1-Q3 were graded by `planned_dates.py` in the job and are re-graded from `rows.csv` by
`test_uk_planned_result.py`. Q4 was graded by reading `planned.csv`; the reading was done by AI
agents working in MV2's name, not by a person.

## The seven snippets (Q4)

| Address | Date read | Snippet | Reading |
|---|---|---|---|
| https://phw.nhs.wales/accessibility-statement/ | 2027-03-31 | `ement was prepared in March 2026. It will be reviewed in March 2027` | planned review |
| https://www.bolton.gov.uk/policies-strategies-procedures/accessibilty/2 | 2025-07-23 | `was prepared on 30 June 2025. It was will be reviewed on 23 July 2025` | planned review |
| https://www.gedling.gov.uk/accessibility-statement | 2026-11-18 | `ement was prepared on 18/11/2025. It will be reviewed on 18/11/2026` | planned review |
| https://www.malvernhills.gov.uk/accessibility | 2023-10-31 | `wed on 23 March 2022. This statement will be reviewed in full again by 31 October 2023` | planned review |
| https://www.redbridge.gov.uk/accessibility-statement/ | 2022-09-21 | `ent was updated on 23 March 2022. It will be reviewed on 21 September 2022` | planned review |
| https://www.redbridge.gov.uk/accessibility-statement/ | 2022-09-21 | `as last updated on 23 March 2022 and will be reviewed on 21 September 2022` | planned review |
| https://www.westminster.gov.uk/accessibility | 2026-10-01 | `y Advisory and Support Service (EASS) . Next Last updated: 1 October 2026` | not planned: a "Next" link, then the page's last update |

The Westminster page was read once more by AI agents on 2026-11-13 at about 19:55 UTC: "Next" is a
link to the next section of the council's accessibility guide, followed by a feedback button and
then "Last updated: 1 October 2026". The page gives no prepared or review sentence, so without that
date it reads as undated.

## What else the job saw (described, not graded)

- 130 of the 470 statements (27.66%) use a future-review phrase ("will be reviewed", "next review"
  and the like), but the census reader took a planned date from only 5 of them.
- Three of the five statements with a true planned date promise a review by a day that had already
  passed when they were read: Redbridge (21 September 2022), Malvern Hills (31 October 2023) and
  Bolton (23 July 2025).
- Exactly 2 statements in the frame carry a census date later than the day of this re-read
  (phw.nhs.wales: 2027-03-31; gedling.gov.uk: 2026-11-18), and both are planned reviews. This
  confirms, for phw.nhs.wales, the guess in [NHS-STOCK-RESULT.md](../nhs-trusts/NHS-STOCK-RESULT.md)
  that its date after the census was a planned review read as a review.
- 313 of the 470 texts (66.60%) are byte for byte the text the census read, and the census reader
  gives the same date as in the census for 461 (98.09%).
- Old reading: 24 undated, 396 dated from a "reviewed / updated" line and 50 from a "prepared /
  published" line. New reading: 25 undated, 392 and 53.

## A fix for the planned-date rule (found after the run)

A date phrase that starts with "last" ("last updated", "last reviewed") is in the past by its own
words. With that one exception added to the rule, checked here on the saved rows and snippets (not
pre-registered), the six true planned snippets are still left out, the Westminster date is kept, 0
dated statements change side of the line, and the councils' share stays 101 of 265 (38.11%).
a11y-statement-check has used the same rule since 0.7.0, so MV2 plans to add this exception there
in a later release.

## What it does not say

A date is what a statement says, read by a pattern. A planned review date is useful information for
readers, and a statement whose date changes here is not wrong or in breach. This study does not test
whether any website is accessible.

## Files

- `rows.csv` (one row per address), `planned.csv` (one row per planned date, snippet at most 120
  characters), `result.json` and `result.txt`: the job's output, unchanged. No other page text is
  kept.
- `test_uk_planned_result.py` (repository root) rebuilds the frame from the two census tables,
  re-grades every measure, gate and prediction from `rows.csv`, replays the planned-date rule on
  every kept snippet, applies the Q4 reading and the "last" exception, and checks every figure in
  this note: `python -m unittest discover -p test_uk_planned_result.py`.
