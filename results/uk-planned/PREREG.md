# uk-planned: how often a planned review date was read as the latest review (pre-registration)

Committed on 2026-11-11, before any statement address is read again for this study. Made by MV2
of Munim, Inc. with AI agents; not yet checked by a person. Code Apache-2.0; this text CC BY 4.0.

## Why

MV2's two UK censuses ([council-stock](../uk-councils/COUNCIL-STOCK-RESULT.md), 2026-11-10, and
[govuk-stock](../govuk-orgs/GOVUK-STOCK-RESULT.md), 2026-11-11) read each statement's date with
the date reader of `council_stock.py` 0.1.0. That reader takes any date after "reviewed in / on"
or "updated in / on" as a review date, so "It will be reviewed in March 2027" reads as a review in
March 2027. Grading govuk-stock found one such statement, but only because its date was later than
the census; a planned date that is already past (for example "will be reviewed in October 2026")
cannot be told apart in the stored tables, which keep no page text. Both censuses report the share
of dated statements dated before 2025-11-01 (councils 105 of 271, 38.75%; organisations 81 of 191,
42.41%). A planned date can make an old statement look current, so these shares could be too low.

Release v0.7.0 of [a11y-statement-check](https://github.com/munimtechnologies/a11y-statement-check)
leaves out a date right after "will be", "shall be", "should be", "must be", "to be" or "next"
(its PLANNED_RE, looking back 25 characters). This study measures how much that changes.

## What was looked at before this plan

Only the two published results and their tables (hosts.csv, which keep the address, the date and
a hash of the text, but no text), and the one planned review quoted in GOVUK-STOCK-RESULT.md. No
statement address has been read again for this study.

## Method

- **Frame (F1).** Every row with status `ok` in `results/uk-councils/hosts.csv` (284 rows) and
  `results/govuk-orgs/hosts.csv` (202 rows), one item per distinct statement address (addresses
  withheld for the publishing tool's blocked word are left out). F1 holds when the two tables have
  exactly 284 and 202 such rows and there are between 400 and 486 distinct addresses; otherwise
  nothing is read.
- **Pins (P0).** `planned_dates.py` 0.1.0 with the unchanged `council_stock.py` 0.1.0 (its date
  reader, statement test and helpers) and `statement_template_check.py` 0.3.0 (byte-identical to
  release v0.3.0, as checked by council_stock). The planned-date rule is copied byte for byte from
  release v0.7.0, and the job checks that the release still has it. If any pin fails, nothing is
  read.
- **Reading.** Each address is read once, in an order fixed by a hash, robots.txt honoured, with a
  pause after each request and one retry after 429 or 503. A page counts as read again when it
  answers 200 with HTML that council_stock still takes as a statement.
- **Two readings of the same text.** The census reader as it is ("old") and the same reader with
  planned dates left out ("new"). Both read the same text, so any difference comes from planned
  dates alone, not from pages changed since the censuses.
- **Kept.** Per address: status, text length and hash, both readings' dates, the number of planned
  dates and the number of future-review phrases (any "will be reviewed", "due to be updated",
  "next review" and the like, whether or not a date follows). For each planned date only a snippet
  of at most 120 characters is kept, so a person can check it. No other page text.

## Gate and predictions

- **G1:** at least 80% of the frame's addresses are read again as a statement. If G1 fails, the
  measures are reported but no prediction is graded.
- **Q1:** at most 5% of the statements read again have a planned date that the old reader took.
- **Q2:** of the statements the old reader dates, at most 1% go from current (dated 2025-11-01 or
  later) to dated before 2025-11-01 or undated when planned dates are left out (graded only with
  at least 100 dated statements).
- **Q3:** for each census separately (councils, organisations), the share of dated statements
  dated before 2025-11-01 changes by at most 1.5 percentage points between the two readings
  (graded only with at least 100 dated statements in each reading of each census).
- **Q4:** of the snippets kept for planned dates, at most 1 snippet, read by eye, is not about a
  planned or scheduled review, update or publication. Graded from `planned.csv` when the result is
  written; the reading is done by AI agents working in MV2's name unless a person does it, and the
  result will say which.

Q1-Q3 are graded by `planned_dates.py` itself; the result note will re-grade them from the saved
table with a test.

## What it will not say

A date is what a statement says, read by a pattern. A statement whose date changes here is not
wrong or in breach: a planned review date is useful information for readers. This study only asks
how often a simple date reader is misled by it, and whether the two censuses' published shares
still stand. It does not test whether any website is accessible.
