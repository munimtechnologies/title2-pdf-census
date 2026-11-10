# council-reread: do stale UK council accessibility statements get a newer date? (pre-registration)

Registered 2026-11-10, before any page is read for this study. Script: `council_reread.py` 0.1.0
with its offline tests (`test_council_reread.py`). Made by MV2 of Munim, Inc. with AI agents; not
yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0.

## Why

MV2's census of the UK's principal councils ([COUNCIL-STOCK-RESULT.md](COUNCIL-STOCK-RESULT.md),
read on 2026-11-10) found that 105 of the 271 dated council accessibility statements (38.75%)
carry a date before 1 November 2025, more than a year old, although GOV.UK's sample statement asks
public sector bodies to review their statement at least once a year (SI 2018/952, regulation 8,
asks for regular review). A single census cannot say whether those dates are about to move. This
study reads the same statements again about two months later, with the same reader, and counts
how many carry a newer date. We found no published panel that re-reads the same public sector
accessibility statements to see whether their dates change; earlier reviews (accessibility.build's
"State of accessibility statements, 2026", Watling Labs' parish review) are single snapshots.

## Panel (fixed now)

The 284 statements that `council_stock.py` 0.1.0 found and read on 2026-11-10: the rows of
`hosts.csv` in this folder with status `ok` (the table is 99,491 bytes, 379 rows, SHA-256
d2f696ed2158...; unchanged since the census). By the date each statement gave in November:

- stale: 105 dated before 2025-11-01;
- due: 15 dated 2025-11-01 to 2025-12-31, which turn a year old before or during the wave;
- fresh: 151 dated 2026;
- undated: 13 with no date the reader could take.

86 of the 284 named WCAG 2.1 as the highest version in November, 191 named 2.2 and 7 none.

## Method

- Wave J: the job runs once, on one day between 2027-01-11 and 2027-01-31. The script refuses to
  read anything outside those dates. (A later wave may follow, pre-registered separately.)
- Order: statements sorted by SHA-256 of the seed `council-reread-2027-01` plus the host; 4 hosts
  at a time; for each host one request at a time with a 1-second pause after each; `robots.txt` is
  read first and a page it disallows is not requested; a 429 or 503 is asked once more after 30
  seconds.
- First the address saved in November is read. It counts as the statement when it answers 200
  with HTML, is not a home page, and passes `council_stock.py`'s statement test (at least 200
  characters of visible text, says "accessibility statement", names WCAG or the enforcement
  procedure).
- If it does not, the statement is looked for again exactly as in November, with
  `council_stock.read_one` (home page link, one hop from a page that links to it, then
  `/accessibility-statement` and `/accessibility`).
- Reader: the same pinned code as in November, `council_stock.py` 0.1.0 and
  `statement_template_check.py` 0.3.0, each checked against the SHA-256 recorded in November's
  `result.json` before anything is read. So a changed date is a change on the page, not in the
  reader. The statement's date is the later of its latest "last reviewed / updated" date and its
  latest "prepared / published on" date.
- A statement has a newer date when both waves give it a date and January's is later.
- Stored per statement: November's date, version, text hash and address; January's status, how it
  was found, address, text length and SHA-256, placeholder rule ids, version, dates and flags. No
  page text and no person's name is stored.

## Gates (nothing is graded unless all hold)

- P0: this file is on main, and both pinned scripts match November's hashes.
- W1: the job runs between 2027-01-11 and 2027-01-31.
- F1: `hosts.csv` matches the bytes above, with 284 read statements, 105 of them stale.
- G1 (at least 80% of the 284 statements read again), at the saved address or found again.

## Predictions (fixed before any page is read)

- R1 (at most 20% of the re-read statements dated before 2025-11-01 carry a newer date in
  January). Statements that went more than a year without a new date mostly stay that way over two
  more months. Graded only with at least 60 re-read stale statements.
- R2 (at least 35% of the dated re-read statements carry a date before 2026-01-01), that is, more
  than a year before the wave. Graded only with at least 150 dated re-read statements.
- R3 (at most 15% of the re-read statements that named WCAG 2.1 as the highest version in November
  name WCAG 2.2 in January). Graded only with at least 50 such statements.

The result is published whether the predictions hold or not.

## Described, not graded

Status of every statement, whether it was read at the saved address or found again, and why not
(robots.txt, no answer, moved); statements whose address or text changed; statements whose text
changed but whose date did not; dates lost or moved earlier; the month of each newer date; newer
dates in each November group (stale, due, fresh, undated) and, for the stale group, by kind of
council; statement years, highest WCAG version and placeholders in January.

## Limits

A date is what a statement says. A council may review its statement without changing the date, or
change the date without reviewing it, and a recent date says nothing about whether the statement
is accurate or the website accessible. A text hash changes with any visible change on the page
(menus, banners, news), so a changed hash is not proof that the statement itself was edited. A
statement that cannot be read in January (moved where the reader cannot find it, refused by a
firewall) drops out of the denominators. Nothing here calls a council in breach of the
regulations.
