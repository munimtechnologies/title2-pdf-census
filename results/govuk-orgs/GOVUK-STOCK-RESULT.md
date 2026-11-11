# govuk-stock: what the accessibility statements of UK government organisations with their own website say (result)

Graded 2026-11-11 from sealed job govuk-stock-v1; the 283 hosts were read from 03:01:35 to 03:10:32 UTC on 2026-11-11.
Plan: [PREREG.md](PREREG.md), committed on 2026-11-10 before any organisation's own website was
read. Scripts: `govuk_stock.py` 0.1.0 and `govuk_frame.py` 0.1.0, with the unchanged
`council_stock.py` 0.1.0 and `statement_template_check.py` 0.3.0. Data: [hosts.csv](hosts.csv),
[govuk-frame.csv](govuk-frame.csv), [govuk-frame.json](govuk-frame.json),
[result.json](result.json) and [result.txt](result.txt), all as the job wrote them. Made by MV2 of
Munim, Inc. with AI agents; not yet checked by a person. Code Apache-2.0; this text and MV2's data
CC BY 4.0. Organisation names, statuses and addresses come from GOV.UK (Open Government Licence
v3.0).

**Two of the four predictions held (O2, O4); O1 and O3 failed.**

**81 of the 191 dated statements (42.41%) carry a date before 1 November 2025**, more than a year
before this census, against 105 of 271 (38.75%) for the UK's principal councils read the same way
([COUNCIL-STOCK-RESULT.md](../uk-councils/COUNCIL-STOCK-RESULT.md)). GOV.UK's sample statement
asks for a review at least once a year. A statement was found on 202 of the 283 own hosts (71.38%), short of the predicted 75%, and 139 of the 202 (68.81%) name WCAG 2.2 as the highest version, just short of the predicted 70% and close to the councils' 67.25%.

## The frame

GOV.UK's organisations API listed 1,273 organisations on 2026-11-11 (SHA-256 of the list
`b8c4498edce6`). 317 of them have the status exempt (302), joining (14) or transitioning (1); 305 of those have a website address in their content item, 1 content item could not be read (financial-remedies-court), and 0 rows were dropped by the publishing tool's blocked word.
The own hosts of 304 organisations make 283 distinct hosts; 14 hosts are shared by several organisations.
The frame file is `govuk-frame.csv` (`8ba68f9f47cb`, 61,627 bytes). A frame-only job
(govuk-frame-v1), which read GOV.UK's API only and ran after this plan was committed, had built a
byte-identical frame the evening before.

Gates: P0 held (the plan was on main and the checker matched release v0.3.0); F1 held (1,273 organisations, 1 content item unread, 0 rows dropped, 283 hosts); G1 held: 278 of the 283 hosts answered (98.23%).

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| O1: own hosts serving a statement found this way | at least 75% | 202 of 283 (71.38%) | no |
| O2: hosts whose statement keeps a 0.3.0 placeholder | at most 3 | 1 (newcoventgardenmarket.com) | yes |
| O3: read statements naming WCAG 2.2 as the highest version | at least 70% | 139 of 202 (68.81%) | no |
| O4: dated statements dated before 2025-11-01 | at least 25% | 81 of 191 (42.41%) | yes |

## Where no statement was found

The reader found no statement on 81 hosts. 16 refused it through robots.txt and 5 did not answer at all. The other 60 answered, but no statement was found through the home page's link, one more
hop, or the two fixed addresses. 15 of those 60 home pages answered 403 (Forbidden), which usually
means a firewall turned the reader away, and 5 more answered 202, 405 or 502. Leaving out the 36 hosts that refused or blocked the reader (robots.txt, no answer, or a 403 home page), a statement was found on 202 of 247 (81.78%). That figure was chosen after the run and is not graded. As the
plan says, a statement not found here is not proof that an organisation has none: some of these
bodies may publish theirs on another site or as a PDF, and public service broadcasters, for one,
are outside the regulations.

## The statements found

The 202 statements cover 216 organisations. 160 use GOV.UK's compliance sentence. 139 name WCAG 2.2 as the highest version, 57 name 2.1 and 6 name no WCAG version. 11 give no date the reader could take; of the 191 dated, 168 take their date from a "last reviewed" or "updated" line and 23 from a "prepared" or "published" line. 22 statements are served on another host than the one GOV.UK names; for example, 6 research council hosts link to UK Research and Innovation's one statement on ukri.org. The 202 pages hold 193 distinct texts. 188 were found through the home page's link, 7 one hop further, and 7 at a fixed address (4 at /accessibility-statement, 3 at /accessibility).

By year of the statement's date: 2020 (5), 2021 (10), 2022 (4), 2023 (18), 2024 (17), 2025 (33), 2026 (103), 2027 (1).

One statement keeps a placeholder: newcoventgardenmarket.com still carries GOV.UK's sample
instruction "[insert one of the following ...]" (rule gov-uk/insert_one_of).

## By type of organisation

GOV.UK's own types; a host is counted under the first of its organisations by slug.

| Type | Hosts | Statement found | WCAG 2.2 | Dated | Dated before 1 Nov 2025 |
|---|---|---|---|---|---|
| advisory_ndpb | 17 | 12 | 5 | 11 | 9 |
| devolved_administration | 3 | 3 | 2 | 3 | 3 |
| executive_agency | 11 | 9 | 4 | 9 | 4 |
| executive_ndpb | 101 | 76 | 53 | 71 | 24 |
| independent_monitoring_body | 3 | 2 | 2 | 1 | 0 |
| non_ministerial_department | 8 | 7 | 5 | 7 | 3 |
| other | 95 | 64 | 46 | 60 | 27 |
| public_corporation | 18 | 7 | 5 | 7 | 3 |
| special_health_authority | 4 | 4 | 4 | 4 | 1 |
| sub_organisation | 19 | 15 | 11 | 15 | 6 |
| tribunal | 4 | 3 | 2 | 3 | 1 |

Among executive non-departmental public bodies, 24 of 71 dated statements (33.80%) carry a date before 1 November 2025; among hosts GOV.UK types as "other", 27 of 60 (45.00%).

## Found after the run (not pre-registered)

- **Counted once per text.** Several hosts serve the same statement (seven UK Research and
  Innovation hosts, three Royal Navy museum hosts). Counted once per distinct text, 78 of 182 dated texts (42.86%) carry a date before 1 November 2025.
- **A planned review read as a review.** 1 statement date is later than the census: the page says
  "It will be reviewed in March 2027", and the reader takes "reviewed in" followed by a date as a
  review date. So a planned next review can be counted as the latest review, which makes a
  statement look newer than it is. Only a date after the census shows this; an earlier planned date
  (for example "will be reviewed in October 2026") cannot be told apart in the stored data, which
  keeps no page text. O4 is not changed by this one statement: counted as undated, it would be 81 of 190 (42.63%). The council census used the same reader. MV2's free a11y-statement-check
  shares this date reader, and a fix that keeps future-tense review dates apart is planned.

## Compared with the councils

| | UK principal councils (2026-11-10) | Organisations with their own website (2026-11-11) |
|---|---|---|
| Statement found | 284 of 379 hosts (74.93%) | 202 of 283 hosts (71.38%) |
| WCAG 2.2 the highest version | 191 of 284 (67.25%) | 139 of 202 (68.81%) |
| Dated before 1 November 2025 | 105 of 271 (38.75%) | 81 of 191 (42.41%) |
| Template placeholder | 1 host | 1 host |

The plan expected these centrally monitored bodies to do at least as well as councils on finding a
statement and on WCAG 2.2. They did about as well on WCAG 2.2 and worse on finding one, and a
larger share of their dated statements carries a date more than a year old.

## Limits

GOV.UK's status and address are what GOV.UK said on the day; an organisation may run several
sites, and only the one GOV.UK names was read. Not every organisation in the frame is covered by
the regulations. A statement linked only from another page, served on another site, published as a
PDF, or behind a firewall that refuses this reader is missed. A date is what the statement says,
read by a pattern, not when it was really reviewed (see the planned-review case above), and an
up-to-date date says nothing about whether the statement is accurate. One page per host, read
once, on one day. This counts what statements say; it does not test whether a website is
accessible, and nothing here calls an organisation in breach.

## Files

- `hosts.csv`: one row per host, with its organisation, the status of the read, how the statement
  was found, its address, text length and SHA-256, rule ids, WCAG version, dates and flags (no page
  text, no person's name).
- `govuk-frame.csv`, `govuk-frame.json`: the frame the job built from GOV.UK's API.
- `result.json`, `result.txt`: the job's output, unchanged.
- `test_govuk_stock_result.py` (repository root): rebuilds the frame's hosts from `govuk-frame.csv`
  with the pinned `govuk_stock.py`, re-grades every measure, gate, prediction and described count
  from `hosts.csv`, and checks every figure in this note.
