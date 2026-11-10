# council-stock result: the accessibility statements of the UK's principal councils

Pre-registered in [PREREG.md](PREREG.md) on 2026-11-09, before any council website was read. Run
once by sealed job council-stock-v1 (02:11 to 02:21 UTC on 2026-11-10) with `council_stock.py`
0.1.0 and the pinned checker `statement_template_check.py` 0.3.0 (release v0.3.0 of MV2's free
[a11y-statement-check](https://github.com/munimtechnologies/a11y-statement-check)). The run's
table ([hosts.csv](hosts.csv)), [result.json](result.json) and [result.txt](result.txt) are here
unchanged, and `test_council_stock_result.py` at the root of this repository re-grades every
figure below from them. Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
Code Apache-2.0; this text and the data CC BY 4.0.

**Three of the four predictions held (N2, N3, N4) and one failed (N1).**

**284 of the 379 principal-council website hosts (74.93%) serve an accessibility statement that
this method found and read**, covering 289 of the 385 councils (75.06%).

## Predictions

| Prediction | Registered | Result | Held |
|---|---|---|---|
| N1: statement found | at least 85% of hosts | 284 of 379 (74.93%) | no |
| N2: statement keeps a 0.3.0 placeholder | at most 5 hosts | 1 host | yes |
| N3: WCAG 2.2 named as the highest version | at least 60% of read statements | 191 of 284 (67.25%) | yes |
| N4: statement dated before 2025-11-01 | at least 25% of dated statements | 105 of 271 (38.75%) | yes |

Gates: the pre-registration was on main and the checker matched release v0.3.0 (P0). The frame is
the 385 councils on 379 hosts registered in `council-frame.csv`, byte for byte (F1). 370 of 379
hosts (97.63%) answered, above G1's 90%.

## Why N1 failed: most of the gap is access, not absence

9 hosts did not answer at all, and for 38 the home page was not requested because robots.txt
disallowed it or answered 401 or 403, which the reader takes as a refusal. Another 19 answered the
home page with another status (13 of them 403) and no statement was found, so for most of those 66
hosts this reader never saw a page it could follow. Of the 313 hosts whose home page answered 200,
284 (90.73%) led to a statement; on the other 29, none was found this way. Of the 332 hosts that
answered and did not refuse the reader by robots.txt, 284 (85.54%) led to a statement, just above
N1's 85%, but N1 was registered on all 379 hosts and is graded that way: it failed.

A statement that was not found here may still exist (linked only from another page, served as a
PDF, or behind a firewall that refuses automated readers), so these counts say nothing about any
one council lacking a statement.

How the 284 were found: 260 were found through the home page's own link, 19 one hop further on, and
5 at a fixed address (`/accessibility-statement` or `/accessibility`). 5 statements were served
from another host and every one of the 284 texts is different. No statement link pointed to another
site and no host answered 429 or 503.

## WCAG version

191 of the 284 statements (67.25%) name WCAG 2.2 as the highest version, 86 (30.28%) name 2.1 and 7
name no version. 233 (82.04%) carry GOV.UK's compliance sentence ("This website is partially
compliant with the Web Content Accessibility Guidelines ..."). The Government Digital Service
announced in January 2024 that it would monitor public sector websites against WCAG 2.2 AA from
October 2024
([GDS accessibility blog](https://accessibility.blog.gov.uk/2024/01/11/get-to-wcag-2-2-faster-with-the-gov-uk-design-system)).

## How old the statements are

GOV.UK's sample statement says a statement must be reviewed at least once a year, and regulation 8
of SI 2018/952 asks for regular review. 271 of the 284 statements give a date that the reader could
take (244 dated by their last review or update, 27 by their preparation) and 13 give none.

**105 of the 271 dated statements (38.75%) carry a date before 1 November 2025**, more than a year
before this census. 76 of them (28.04% of the dated) are dated 2024 or earlier. At the other end,
151 (55.72%) are dated in 2026, and 20 of those 151 dated in 2026 still name WCAG 2.1 as the highest
version.

A date is what the statement says. A council may review a statement without changing its date, and
a recent date says nothing about whether the statement is accurate or the website accessible. The
date reader takes the latest date after words such as "last reviewed", "last updated", "prepared
on"; it was tested offline, but its readings of these 284 pages have not been checked by a person.

## By kind of council

| Kind | Hosts | Statement found | Names WCAG 2.2 | Dated | Dated before 2025-11-01 |
|---|---|---|---|---|---|
| English counties | 23 | 19 | 16 | 19 | 6 (31.58%) |
| English districts | 161 | 126 | 84 | 118 | 46 (38.98%) |
| Metropolitan boroughs | 36 | 26 | 14 | 25 | 13 (52.00%) |
| English unitaries | 61 | 41 | 29 | 40 | 14 (35.00%) |
| London boroughs | 33 | 30 | 18 | 29 | 17 (58.62%) |
| Northern Irish districts | 11 | 10 | 6 | 10 | 2 (20.00%) |
| Scottish councils | 32 | 22 | 18 | 21 | 5 (23.81%) |
| Welsh unitaries | 22 | 10 | 6 | 9 | 2 (22.22%) |

A host shared by several councils is counted once, under the kind of the first council by name.
London boroughs have the largest share of statements dated before 1 November 2025 (17 of 29,
58.62%). Welsh unitary councils have the lowest share found (10 of 22 hosts, 45.45%); several of
their sites are bilingual, and the link and address rules may suit them less well, so this is a
limit of the method as much as a finding.

## Placeholders

Unlike England's school websites (see [SCHOOL-STOCK-RESULT.md](../uk-schools/SCHOOL-STOCK-RESULT.md),
667 hosts with an unfinished template), council statements are almost always filled in. One
statement (mansfield.gov.uk) keeps one field of GOV.UK's sample statement, "[example of
non-essential document]"; no other 0.3.0 rule flags it.

## Comparison with earlier work

accessibility.build's "State of accessibility statements, 2026" (data of 2 September 2026) found a
statement for 206 of 303 local authorities (67.99%) and scored which required sections each has,
with 34 of the 206 giving no date. Its frame and method differ (303 authorities, its own crawler),
so the two shares are not directly comparable. This census adds what that review does not report:
the WCAG version each statement names, how old its stated date is, and whether template fields
were left in.

## Limits

One read of one page per council, on one day, by an automated reader that honours robots.txt and
that some councils' firewalls refuse. A statement linked only from another page, published as a
PDF, or served on another site that the rules do not reach is missed. The placeholder rules are
0.3.0's, unchanged; the date reader is `council_stock.py`'s, unchanged. Nothing here says that a
council is in breach of the regulations, and nothing here tests whether a website is accessible.

## Reproduce

`python -m unittest discover -p test_council_stock_result.py` at the root of this repository
re-grades every measure, gate and prediction from `hosts.csv` with the pinned scripts and checks
each figure in this note. `python council_stock.py --out-dir out` runs the census again (it reads
live websites, so the counts will differ).
